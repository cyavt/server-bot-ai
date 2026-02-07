package xiaozhi.modules.device.service.impl;

import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.Base64;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TimeZone;
import java.util.UUID;
import java.util.stream.Collectors;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

import org.apache.commons.lang3.StringUtils;
import org.springframework.aop.framework.AopContext;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;

import cn.hutool.core.date.DatePattern;
import cn.hutool.core.date.DateUtil;
import cn.hutool.core.map.MapUtil;
import cn.hutool.core.util.RandomUtil;
import cn.hutool.core.util.StrUtil;
import cn.hutool.crypto.digest.DigestUtil;
import cn.hutool.http.ContentType;
import cn.hutool.http.Header;
import cn.hutool.http.HttpRequest;
import cn.hutool.json.JSONUtil;
import jakarta.servlet.http.HttpServletRequest;
import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.redis.RedisKeys;
import xiaozhi.common.redis.RedisUtils;
import xiaozhi.common.service.impl.BaseServiceImpl;
import xiaozhi.common.user.UserDetail;
import xiaozhi.common.utils.ConvertUtils;
import xiaozhi.common.utils.DateUtils;
import xiaozhi.common.utils.ToolUtil;
import xiaozhi.modules.device.dao.DeviceDao;
import xiaozhi.modules.device.dto.DeviceManualAddDTO;
import xiaozhi.modules.device.dto.DevicePageUserDTO;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.entity.OtaEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.device.service.OtaService;
import xiaozhi.modules.device.vo.UserShowDeviceListVO;
import xiaozhi.modules.security.user.SecurityUser;
import xiaozhi.modules.sys.service.SysParamsService;
import xiaozhi.modules.sys.service.SysUserUtilService;

@Slf4j
@Service
@AllArgsConstructor
public class DeviceServiceImpl extends BaseServiceImpl<DeviceDao, DeviceEntity> implements DeviceService {

    private final DeviceDao deviceDao;
    private final SysUserUtilService sysUserUtilService;
    private final SysParamsService sysParamsService;
    private final RedisUtils redisUtils;
    private final OtaService otaService;

    @Async
    public void updateDeviceConnectionInfo(String agentId, String deviceId, String appVersion) {
        try {
            DeviceEntity device = new DeviceEntity();
            device.setId(deviceId);
            device.setLastConnectedAt(new Date());
            if (StringUtils.isNotBlank(appVersion)) {
                device.setAppVersion(appVersion);
            }
            deviceDao.updateById(device);
            if (StringUtils.isNotBlank(agentId)) {
                redisUtils.set(RedisKeys.getAgentDeviceLastConnectedAtById(agentId), new Date());
            }
        } catch (Exception e) {
            log.error("Cập nhật thông tin kết nối thiết bị bất đồng bộ thất bại", e);
        }
    }

    @Override
    public Boolean deviceActivation(String agentId, String activationCode) {
        if (StringUtils.isBlank(activationCode)) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_EMPTY);
        }
        String deviceKey = RedisKeys.getOtaActivationCode(activationCode);
        Object cacheDeviceId = redisUtils.get(deviceKey);
        if (ToolUtil.isEmpty(cacheDeviceId)) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_ERROR);
        }
        String deviceId = (String) cacheDeviceId;
        String safeDeviceId = deviceId.replace(":", "_").toLowerCase();
        String cacheDeviceKey = RedisKeys.getOtaDeviceActivationInfo(safeDeviceId);
        Map<String, Object> cacheMap = (Map<String, Object>) redisUtils.get(cacheDeviceKey);
        if (ToolUtil.isEmpty(cacheMap)) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_ERROR);
        }
        String cachedCode = (String) cacheMap.get("activation_code");
        if (!activationCode.equals(cachedCode)) {
            throw new RenException(ErrorCode.ACTIVATION_CODE_ERROR);
        }
        // Kiểm tra xem thiết bị đã được kích hoạt chưa
        if (selectById(deviceId) != null) {
            throw new RenException(ErrorCode.DEVICE_ALREADY_ACTIVATED);
        }

        String macAddress = (String) cacheMap.get("mac_address");
        String board = (String) cacheMap.get("board");
        String appVersion = (String) cacheMap.get("app_version");
        UserDetail user = SecurityUser.getUser();
        if (user.getId() == null) {
            throw new RenException(ErrorCode.USER_NOT_LOGIN);
        }

        Date currentTime = new Date();
        DeviceEntity deviceEntity = new DeviceEntity();
        deviceEntity.setId(deviceId);
        deviceEntity.setBoard(board);
        deviceEntity.setAgentId(agentId);
        deviceEntity.setAppVersion(appVersion);
        deviceEntity.setMacAddress(macAddress);
        deviceEntity.setUserId(user.getId());
        deviceEntity.setCreator(user.getId());
        deviceEntity.setAutoUpdate(1);
        deviceEntity.setCreateDate(currentTime);
        deviceEntity.setUpdater(user.getId());
        deviceEntity.setUpdateDate(currentTime);
        deviceEntity.setLastConnectedAt(currentTime);
        deviceDao.insert(deviceEntity);

        // Xóa bộ nhớ đệm redis, xóa bộ nhớ đệm số lượng thiết bị của agent
        redisUtils.delete(List.of(cacheDeviceKey, deviceKey, RedisKeys.getAgentDeviceCountById(agentId)));
        return true;
    }

    /**
     * Lấy dữ liệu thiết bị trực tuyến
     */
    @Override
    public String getDeviceOnlineData(String agentId) {
        // Lấy địa chỉ cổng MQTT từ tham số hệ thống
        String mqttGatewayUrl = sysParamsService.getValue("server.mqtt_manager_api", true);
        if (StringUtils.isBlank(mqttGatewayUrl) || "null".equals(mqttGatewayUrl)) {
            return "";
        }
        // Xây dựng URL đầy đủ
        String url = StrUtil.format("http://{}/api/devices/status", mqttGatewayUrl);

        // Lấy danh sách thiết bị của người dùng hiện tại
        UserDetail user = SecurityUser.getUser();
        List<DeviceEntity> devices = getUserDevices(user.getId(), agentId);

        // Xây dựng mảng deviceIds
        Set<String> deviceIds = devices.stream().map(o -> {
            String macAddress = Optional.ofNullable(o.getMacAddress()).orElse("unknown").replace(":", "_");
            String groupId = Optional.ofNullable(o.getBoard()).orElse("GID_default").replace(":", "_");
            return StrUtil.format("{}@@@{}@@@{}", groupId, macAddress, macAddress);
        }).collect(Collectors.toSet());

        // Xây dựng tham số đầu vào của yêu cầu
        Map<String, Set<String>> params = MapUtil
                .builder(new HashMap<String, Set<String>>())
                .put("clientIds", deviceIds).build();

        if (ToolUtil.isNotEmpty(deviceIds)) {
            // Gửi yêu cầu
            String resultMessage = HttpRequest.post(url)
                    .header(Header.CONTENT_TYPE, ContentType.JSON.getValue())
                    .header(Header.AUTHORIZATION, "Bearer " + generateBearerToken())
                    .body(JSONUtil.toJsonStr(params))
                    .timeout(10000) // Hết thời gian chờ, tính bằng mili giây
                    .execute().body();
            return resultMessage;
        }
        // Trả về phản hồi
        return "";
    }

    @Override
    public DeviceReportRespDTO checkDeviceActive(String macAddress, String clientId, DeviceReportReqDTO deviceReport) {
        DeviceReportRespDTO response = new DeviceReportRespDTO();
        response.setServer_time(buildServerTime());

        DeviceEntity deviceById = getDeviceByMacAddress(macAddress);

        // Nếu thiết bị chưa được liên kết, trả về thông tin firmware hiện tại đã tải lên (không cập nhật) để tương thích với phiên bản firmware cũ
        if (deviceById == null) {
            DeviceReportRespDTO.Firmware firmware = new DeviceReportRespDTO.Firmware();
            firmware.setVersion(deviceReport.getApplication().getVersion());
            firmware.setUrl(Constant.INVALID_FIRMWARE_URL);
            response.setFirmware(firmware);
        } else {
            // Chỉ trả về thông tin nâng cấp firmware khi thiết bị đã được liên kết và autoUpdate khác 0
            if (deviceById.getAutoUpdate() != 0) {
                String type = deviceReport.getBoard() == null ? null : deviceReport.getBoard().getType();
                DeviceReportRespDTO.Firmware firmware = buildFirmwareInfo(type,
                        deviceReport.getApplication() == null ? null : deviceReport.getApplication().getVersion());
                response.setFirmware(firmware);
            }
        }

        // Thêm cấu hình WebSocket
        DeviceReportRespDTO.Websocket websocket = new DeviceReportRespDTO.Websocket();
        // Lấy WebSocket URL từ tham số hệ thống, nếu chưa cấu hình thì sử dụng giá trị mặc định
        String wsUrl = sysParamsService.getValue(Constant.SERVER_WEBSOCKET, true);

        // Kiểm tra xem có bật xác thực và tạo token không
        String authEnabled = sysParamsService.getValue(Constant.SERVER_AUTH_ENABLED, true);
        if ("true".equalsIgnoreCase(authEnabled)) {
            try {
                // Tạo token
                String token = generateWebSocketToken(clientId, macAddress);
                websocket.setToken(token);
            } catch (Exception e) {
                log.error("Tạo WebSocket token thất bại: {}", e.getMessage());
                websocket.setToken("");
            }
        } else {
            websocket.setToken("");
        }

        if (StringUtils.isBlank(wsUrl) || wsUrl.equals("null")) {
            log.error("Địa chỉ WebSocket chưa được cấu hình, vui lòng đăng nhập vào bảng điều khiển thông minh, tìm cấu hình 【server.websocket】 trong quản lý tham số");
            wsUrl = "ws://xiaozhi.server.com:8000/xiaozhi/v1/";
            websocket.setUrl(wsUrl);
        } else {
            String[] wsUrls = wsUrl.split("\\;");
            if (wsUrls.length > 0) {
                // Chọn ngẫu nhiên một WebSocket URL
                websocket.setUrl(wsUrls[RandomUtil.randomInt(0, wsUrls.length)]);
            } else {
                log.error("Địa chỉ WebSocket chưa được cấu hình, vui lòng đăng nhập vào bảng điều khiển thông minh, tìm cấu hình 【server.websocket】 trong quản lý tham số");
                websocket.setUrl("ws://xiaozhi.server.com:8000/xiaozhi/v1/");
            }
        }

        response.setWebsocket(websocket);

        // Thêm cấu hình MQTT UDP
        // Lấy địa chỉ MQTT Gateway từ tham số hệ thống, chỉ sử dụng khi cấu hình hợp lệ
        String mqttUdpConfig = sysParamsService.getValue(Constant.SERVER_MQTT_GATEWAY, true);
        if (mqttUdpConfig != null && !mqttUdpConfig.equals("null") && !mqttUdpConfig.isEmpty()) {
            try {
                String groupId = deviceById != null && deviceById.getBoard() != null ? deviceById.getBoard()
                        : "GID_default";
                DeviceReportRespDTO.MQTT mqtt = buildMqttConfig(macAddress, groupId);
                if (mqtt != null) {
                    mqtt.setEndpoint(mqttUdpConfig);
                    response.setMqtt(mqtt);
                }
            } catch (Exception e) {
                log.error("Tạo cấu hình MQTT thất bại: {}", e.getMessage());
            }
        }

        if (deviceById != null) {
            // Nếu thiết bị tồn tại, cập nhật bất đồng bộ thời gian kết nối lần cuối và thông tin phiên bản
            String appVersion = deviceReport.getApplication() != null ? deviceReport.getApplication().getVersion()
                    : null;
            // Gọi phương thức bất đồng bộ thông qua proxy Spring
            ((DeviceServiceImpl) AopContext.currentProxy()).updateDeviceConnectionInfo(deviceById.getAgentId(),
                    deviceById.getId(), appVersion);
        } else {
            // Nếu thiết bị không tồn tại, tạo mã kích hoạt
            DeviceReportRespDTO.Activation code = buildActivation(macAddress, deviceReport);
            response.setActivation(code);
        }

        return response;
    }

    @Override
    public List<DeviceEntity> getUserDevices(Long userId, String agentId) {
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("agent_id", agentId);
        return baseDao.selectList(wrapper);
    }

    @Override
    public void unbindDevice(Long userId, String deviceId) {
        // Trước tiên truy vấn thông tin thiết bị, lấy agentId
        DeviceEntity device = baseDao.selectById(deviceId);
        if (device == null) {
            return;
        }
        if (StringUtils.isNotBlank(device.getAgentId())) {
            // Xóa bộ nhớ đệm số lượng thiết bị của agent
            redisUtils.delete(RedisKeys.getAgentDeviceCountById(device.getAgentId()));
        }

        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        wrapper.eq("id", deviceId);
        baseDao.delete(wrapper);
    }

    @Override
    public void deleteByUserId(Long userId) {
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        baseDao.delete(wrapper);
    }

    @Override
    public Long selectCountByUserId(Long userId) {
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("user_id", userId);
        return baseDao.selectCount(wrapper);
    }

    @Override
    public void deleteByAgentId(String agentId) {
        UpdateWrapper<DeviceEntity> wrapper = new UpdateWrapper<>();
        wrapper.eq("agent_id", agentId);
        baseDao.delete(wrapper);
    }

    @Override
    public PageData<UserShowDeviceListVO> page(DevicePageUserDTO dto) {
        Map<String, Object> params = new HashMap<String, Object>();
        params.put(Constant.PAGE, dto.getPage());
        params.put(Constant.LIMIT, dto.getLimit());
        IPage<DeviceEntity> page = baseDao.selectPage(
                getPage(params, "mac_address", true),
                // Định nghĩa điều kiện truy vấn
                new QueryWrapper<DeviceEntity>()
                        // Tìm kiếm theo từ khóa thiết bị bắt buộc
                        .like(StringUtils.isNotBlank(dto.getKeywords()), "alias", dto.getKeywords()));
        // Xử lý vòng lặp dữ liệu trả về từ page, trả về các trường cần thiết
        List<UserShowDeviceListVO> list = page.getRecords().stream().map(device -> {
            UserShowDeviceListVO vo = ConvertUtils.sourceToTarget(device, UserShowDeviceListVO.class);
            // Chuyển thời gian sửa đổi cuối cùng thành thời gian mô tả ngắn gọn
            vo.setRecentChatTime(DateUtils.getShortTime(device.getUpdateDate()));
            sysUserUtilService.assignUsername(device.getUserId(),
                    vo::setBindUserName);
            vo.setDeviceType(device.getBoard());
            return vo;
        }).toList();
        // Tính số trang
        return new PageData<>(list, page.getTotal());
    }

    @Override
    public DeviceEntity getDeviceByMacAddress(String macAddress) {
        if (StringUtils.isBlank(macAddress)) {
            return null;
        }
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("mac_address", macAddress);
        return baseDao.selectOne(wrapper);
    }

    private DeviceReportRespDTO.ServerTime buildServerTime() {
        DeviceReportRespDTO.ServerTime serverTime = new DeviceReportRespDTO.ServerTime();
        TimeZone tz = TimeZone.getDefault();
        serverTime.setTimestamp(Instant.now().toEpochMilli());
        serverTime.setTimeZone(tz.getID());
        serverTime.setTimezone_offset(tz.getOffset(System.currentTimeMillis()) / (60 * 1000));
        return serverTime;
    }

    @Override
    public String geCodeByDeviceId(String deviceId) {
        String dataKey = getDeviceCacheKey(deviceId);

        Map<String, Object> cacheMap = (Map<String, Object>) redisUtils.get(dataKey);
        if (cacheMap != null && cacheMap.containsKey("activation_code")) {
            String cachedCode = (String) cacheMap.get("activation_code");
            return cachedCode;
        }
        return null;
    }

    @Override
    public Date getLatestLastConnectionTime(String agentId) {
        // Truy vấn xem có thời gian cache không, nếu có thì trả về
        Date cachedDate = (Date) redisUtils.get(RedisKeys.getAgentDeviceLastConnectedAtById(agentId));
        if (cachedDate != null) {
            return cachedDate;
        }
        Date maxDate = deviceDao.getAllLastConnectedAtByAgentId(agentId);
        if (maxDate != null) {
            redisUtils.set(RedisKeys.getAgentDeviceLastConnectedAtById(agentId), maxDate);
        }
        return maxDate;
    }

    private String getDeviceCacheKey(String deviceId) {
        String safeDeviceId = deviceId.replace(":", "_").toLowerCase();
        return RedisKeys.getOtaDeviceActivationInfo(safeDeviceId);
    }

    public DeviceReportRespDTO.Activation buildActivation(String deviceId, DeviceReportReqDTO deviceReport) {
        DeviceReportRespDTO.Activation code = new DeviceReportRespDTO.Activation();

        String cachedCode = geCodeByDeviceId(deviceId);

        if (StringUtils.isNotBlank(cachedCode)) {
            code.setCode(cachedCode);
            String frontedUrl = sysParamsService.getValue(Constant.SERVER_FRONTED_URL, true);
            code.setMessage(frontedUrl + "\n" + cachedCode);
            code.setChallenge(deviceId);
        } else {
            String newCode = RandomUtil.randomNumbers(6);
            code.setCode(newCode);
            String frontedUrl = sysParamsService.getValue(Constant.SERVER_FRONTED_URL, true);
            code.setMessage(frontedUrl + "\n" + newCode);
            code.setChallenge(deviceId);

            Map<String, Object> dataMap = new HashMap<>();
            dataMap.put("id", deviceId);
            dataMap.put("mac_address", deviceId);

            dataMap.put("board", (deviceReport.getBoard() != null && deviceReport.getBoard().getType() != null)
                    ? deviceReport.getBoard().getType()
                    : (deviceReport.getChipModelName() != null ? deviceReport.getChipModelName() : "unknown"));
            dataMap.put("app_version", (deviceReport.getApplication() != null)
                    ? deviceReport.getApplication().getVersion()
                    : null);

            dataMap.put("deviceId", deviceId);
            dataMap.put("activation_code", newCode);

            // Ghi key dữ liệu chính
            String dataKey = getDeviceCacheKey(deviceId);
            redisUtils.set(dataKey, dataMap);

            // Ghi key tra cứu ngược mã kích hoạt
            String codeKey = RedisKeys.getOtaActivationCode(newCode);
            redisUtils.set(codeKey, deviceId);
        }
        return code;
    }

    private DeviceReportRespDTO.Firmware buildFirmwareInfo(String type, String currentVersion) {
        if (StringUtils.isBlank(type)) {
            return null;
        }
        if (StringUtils.isBlank(currentVersion)) {
            currentVersion = "0.0.0";
        }

        OtaEntity ota = otaService.getLatestOta(type);
        DeviceReportRespDTO.Firmware firmware = new DeviceReportRespDTO.Firmware();
        String downloadUrl = null;

        if (ota != null) {
            // Nếu thiết bị không có thông tin phiên bản, hoặc phiên bản OTA mới hơn phiên bản thiết bị, thì trả về địa chỉ tải xuống
            if (compareVersions(ota.getVersion(), currentVersion) > 0) {
                String otaUrl = sysParamsService.getValue(Constant.SERVER_OTA, true);
                if (StringUtils.isBlank(otaUrl) || otaUrl.equals("null")) {
                    log.error("Địa chỉ OTA chưa được cấu hình, vui lòng đăng nhập vào bảng điều khiển thông minh, tìm cấu hình 【server.ota】 trong quản lý tham số");
                    // Thử lấy từ yêu cầu
                    HttpServletRequest request = ((ServletRequestAttributes) RequestContextHolder
                            .getRequestAttributes())
                            .getRequest();
                    otaUrl = request.getRequestURL().toString();
                }
                // Thay thế /ota/ trong URL thành /otaMag/download/
                String uuid = UUID.randomUUID().toString();
                redisUtils.set(RedisKeys.getOtaIdKey(uuid), ota.getId());
                downloadUrl = otaUrl.replace("/ota/", "/otaMag/download/") + uuid;
            }
        }

        firmware.setVersion(ota == null ? currentVersion : ota.getVersion());
        firmware.setUrl(downloadUrl == null ? Constant.INVALID_FIRMWARE_URL : downloadUrl);
        return firmware;
    }

    /**
     * So sánh hai số phiên bản
     * 
     * @param version1 Phiên bản 1
     * @param version2 Phiên bản 2
     * @return Nếu version1 > version2 trả về 1, version1 < version2 trả về -1, bằng nhau trả về 0
     */
    private static int compareVersions(String version1, String version2) {
        if (version1 == null || version2 == null) {
            return 0;
        }

        String[] v1Parts = version1.split("\\.");
        String[] v2Parts = version2.split("\\.");

        int length = Math.max(v1Parts.length, v2Parts.length);
        for (int i = 0; i < length; i++) {
            int v1 = i < v1Parts.length ? Integer.parseInt(v1Parts[i]) : 0;
            int v2 = i < v2Parts.length ? Integer.parseInt(v2Parts[i]) : 0;

            if (v1 > v2) {
                return 1;
            } else if (v1 < v2) {
                return -1;
            }
        }
        return 0;
    }

    @Override
    public void manualAddDevice(Long userId, DeviceManualAddDTO dto) {
        // Kiểm tra xem mac đã tồn tại chưa
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.eq("mac_address", dto.getMacAddress());
        DeviceEntity exist = baseDao.selectOne(wrapper);
        if (exist != null) {
            throw new RenException(ErrorCode.MAC_ADDRESS_ALREADY_EXISTS);
        }
        Date now = new Date();
        DeviceEntity entity = new DeviceEntity();
        entity.setId(dto.getMacAddress());
        entity.setUserId(userId);
        entity.setAgentId(dto.getAgentId());
        entity.setBoard(dto.getBoard());
        entity.setAppVersion(dto.getAppVersion());
        entity.setMacAddress(dto.getMacAddress());
        entity.setCreateDate(now);
        entity.setUpdateDate(now);
        entity.setLastConnectedAt(now);
        entity.setCreator(userId);
        entity.setUpdater(userId);
        entity.setAutoUpdate(1);
        baseDao.insert(entity);

        // Thêm: Xóa bộ nhớ đệm số lượng thiết bị của agent
        redisUtils.delete(RedisKeys.getAgentDeviceCountById(dto.getAgentId()));
    }

    @Override
    public List<DeviceEntity> searchDevicesByMacAddress(String macAddress, Long userId) {
        QueryWrapper<DeviceEntity> wrapper = new QueryWrapper<>();
        wrapper.like("mac_address", macAddress);
        wrapper.eq("user_id", userId);
        return deviceDao.selectList(wrapper);
    }

    /**
     * Tạo chữ ký mật khẩu MQTT
     * 
     * @param content   Nội dung chữ ký (clientId + '|' + username)
     * @param secretKey Khóa bí mật
     * @return Chữ ký HMAC-SHA256 được mã hóa Base64
     */
    private String generatePasswordSignature(String content, String secretKey) throws Exception {
        Mac hmac = Mac.getInstance("HmacSHA256");
        SecretKeySpec keySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
        hmac.init(keySpec);
        byte[] signature = hmac.doFinal(content.getBytes(StandardCharsets.UTF_8));
        return Base64.getEncoder().encodeToString(signature);
    }

    /**
     * Tạo token xác thực WebSocket tuân theo logic triển khai AuthManager phía Python: token = signature.timestamp
     * 
     * @param clientId ID khách hàng
     * @param username Tên người dùng (thường là deviceId/macAddress)
     * @return Chuỗi token xác thực
     */
    public String generateWebSocketToken(String clientId, String username)
            throws NoSuchAlgorithmException, InvalidKeyException {
        // Lấy khóa từ tham số hệ thống
        String secretKey = sysParamsService.getValue(Constant.SERVER_SECRET, false);
        if (StringUtils.isBlank(secretKey)) {
            throw new IllegalStateException("Khóa xác thực WebSocket chưa được cấu hình (server.secret)");
        }

        // Lấy dấu thời gian hiện tại (giây)
        long timestamp = System.currentTimeMillis() / 1000;

        // Xây dựng nội dung chữ ký: clientId|username|timestamp
        String content = String.format("%s|%s|%d", clientId, username, timestamp);

        // Tạo chữ ký HMAC-SHA256
        Mac hmac = Mac.getInstance("HmacSHA256");
        SecretKeySpec keySpec = new SecretKeySpec(secretKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256");
        hmac.init(keySpec);
        byte[] signature = hmac.doFinal(content.getBytes(StandardCharsets.UTF_8));

        // Mã hóa chữ ký Base64 URL-safe (loại bỏ ký tự đệm =)
        String signatureBase64 = Base64.getUrlEncoder().withoutPadding().encodeToString(signature);

        // Định dạng trả về: signature.timestamp
        return String.format("%s.%d", signatureBase64, timestamp);
    }

    /**
     * Xây dựng thông tin cấu hình MQTT
     * 
     * @param macAddress Địa chỉ MAC
     * @param groupId    ID nhóm
     * @return Đối tượng cấu hình MQTT
     */
    private DeviceReportRespDTO.MQTT buildMqttConfig(String macAddress, String groupId)
            throws Exception {
        // Lấy khóa chữ ký từ biến môi trường hoặc tham số hệ thống
        String signatureKey = sysParamsService.getValue("server.mqtt_signature_key", true);
        if (StringUtils.isBlank(signatureKey)) {
            log.warn("Thiếu MQTT_SIGNATURE_KEY, bỏ qua việc tạo cấu hình MQTT");
            return null;
        }

        // Xây dựng định dạng ID khách hàng: groupId@@@macAddress@@@uuid
        String groupIdSafeStr = groupId.replace(":", "_");
        String deviceIdSafeStr = macAddress.replace(":", "_");
        String mqttClientId = String.format("%s@@@%s@@@%s", groupIdSafeStr, deviceIdSafeStr, deviceIdSafeStr);

        // Xây dựng dữ liệu người dùng (bao gồm IP và thông tin khác)
        Map<String, String> userData = new HashMap<>();
        // Thử lấy IP khách hàng
        try {
            ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder
                    .getRequestAttributes();
            if (attributes != null) {
                HttpServletRequest request = attributes.getRequest();
                String clientIp = request.getRemoteAddr();
                userData.put("ip", clientIp);
            }
        } catch (Exception e) {
            userData.put("ip", "unknown");
        }

        // Mã hóa dữ liệu người dùng thành Base64 JSON
        String userDataJson = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(userData);
        String username = Base64.getEncoder().encodeToString(userDataJson.getBytes(StandardCharsets.UTF_8));

        // Tạo chữ ký mật khẩu
        String password = generatePasswordSignature(mqttClientId + "|" + username, signatureKey);

        // Xây dựng cấu hình MQTT
        DeviceReportRespDTO.MQTT mqtt = new DeviceReportRespDTO.MQTT();
        mqtt.setClient_id(mqttClientId);
        mqtt.setUsername(username);
        mqtt.setPassword(password);
        mqtt.setPublish_topic("device-server");
        mqtt.setSubscribe_topic("devices/p2p/" + deviceIdSafeStr);

        return mqtt;
    }

    /**
     * Tạo BearerToken
     */
    private String generateBearerToken() {
        try {
            String dateStr = DateUtil.format(new Date(), DatePattern.NORM_DATE_PATTERN);
            String signatureKey = sysParamsService.getValue(Constant.SERVER_MQTT_SECRET, false);
            if (ToolUtil.isEmpty(signatureKey)) {
                return null;
            }
            return DigestUtil.sha256Hex(dateStr + signatureKey);
        } catch (Exception e) {
            return null;
        }
    }

    @Override
    public Object getDeviceTools(String deviceId) {
        // Lấy địa chỉ cổng MQTT từ tham số hệ thống
        String mqttGatewayUrl = sysParamsService.getValue("server.mqtt_manager_api", true);
        if (StringUtils.isBlank(mqttGatewayUrl) || "null".equals(mqttGatewayUrl)) {
            return null;
        }

        // Lấy thông tin thiết bị
        DeviceEntity device = baseDao.selectById(deviceId);
        if (device == null) {
            return null;
        }

        // Kiểm tra xem thiết bị có thuộc về người dùng hiện tại không
        UserDetail user = SecurityUser.getUser();
        if (!device.getUserId().equals(user.getId())) {
            return null;
        }

        // Xây dựng clientId
        String macAddress = Optional.ofNullable(device.getMacAddress()).orElse("unknown").replace(":", "_");
        String groupId = Optional.ofNullable(device.getBoard()).orElse("GID_default").replace(":", "_");
        String clientId = StrUtil.format("{}@@@{}@@@{}", groupId, macAddress, macAddress);

        // Xây dựng URL đầy đủ
        String url = StrUtil.format("http://{}/api/commands/{}", mqttGatewayUrl, clientId);

        // Xây dựng thân yêu cầu
        Map<String, Object> payload = MapUtil
                .builder(new HashMap<String, Object>())
                .put("jsonrpc", "2.0")
                .put("id", 2)
                .put("method", "tools/list")
                .put("params", MapUtil.builder(new HashMap<String, Object>())
                        .put("withUserTools", true)
                        .build())
                .build();

        Map<String, Object> requestBody = MapUtil
                .builder(new HashMap<String, Object>())
                .put("type", "mcp")
                .put("payload", payload)
                .build();

        // 发送请求
        String resultMessage = HttpRequest.post(url)
                .header(Header.CONTENT_TYPE, ContentType.JSON.getValue())
                .header(Header.AUTHORIZATION, "Bearer " + generateBearerToken())
                .body(JSONUtil.toJsonStr(requestBody))
                .timeout(10000) // 超时，毫秒
                .execute().body();

        // Phân tích phản hồi
        if (StringUtils.isNotBlank(resultMessage)) {
            cn.hutool.json.JSONObject jsonObject = JSONUtil.parseObj(resultMessage);
            if (jsonObject.getBool("success", false)) {
                return jsonObject.get("data");
            }
        }

        return null;
    }

    @Override
    public Object callDeviceTool(String deviceId, String toolName, Map<String, Object> arguments) {
        // Lấy địa chỉ cổng MQTT từ tham số hệ thống
        String mqttGatewayUrl = sysParamsService.getValue("server.mqtt_manager_api", true);
        if (StringUtils.isBlank(mqttGatewayUrl) || "null".equals(mqttGatewayUrl)) {
            return null;
        }

        // Lấy thông tin thiết bị
        DeviceEntity device = baseDao.selectById(deviceId);
        if (device == null) {
            return null;
        }

        // Kiểm tra xem thiết bị có thuộc về người dùng hiện tại không
        UserDetail user = SecurityUser.getUser();
        if (!device.getUserId().equals(user.getId())) {
            return null;
        }

        // Xây dựng clientId
        String macAddress = Optional.ofNullable(device.getMacAddress()).orElse("unknown").replace(":", "_");
        String groupId = Optional.ofNullable(device.getBoard()).orElse("GID_default").replace(":", "_");
        String clientId = StrUtil.format("{}@@@{}@@@{}", groupId, macAddress, macAddress);

        // Xây dựng URL đầy đủ
        String url = StrUtil.format("http://{}/api/commands/{}", mqttGatewayUrl, clientId);

        // Xây dựng thân yêu cầu
        Map<String, Object> params = MapUtil
                .builder(new HashMap<String, Object>())
                .put("name", toolName)
                .put("arguments", arguments)
                .build();

        Map<String, Object> payload = MapUtil
                .builder(new HashMap<String, Object>())
                .put("jsonrpc", "2.0")
                .put("id", 2)
                .put("method", "tools/call")
                .put("params", params)
                .build();

        Map<String, Object> requestBody = MapUtil
                .builder(new HashMap<String, Object>())
                .put("type", "mcp")
                .put("payload", payload)
                .build();

        // 发送请求
        String resultMessage = HttpRequest.post(url)
                .header(Header.CONTENT_TYPE, ContentType.JSON.getValue())
                .header(Header.AUTHORIZATION, "Bearer " + generateBearerToken())
                .body(JSONUtil.toJsonStr(requestBody))
                .timeout(10000) // 超时，毫秒
                .execute().body();

        // Phân tích phản hồi
        if (StringUtils.isNotBlank(resultMessage)) {
            cn.hutool.json.JSONObject jsonObject = JSONUtil.parseObj(resultMessage);
            if (jsonObject.getBool("success", false)) {
                cn.hutool.json.JSONObject data = jsonObject.getJSONObject("data");
                if (data != null) {
                    cn.hutool.json.JSONArray content = data.getJSONArray("content");
                    if (content != null && content.size() > 0) {
                        cn.hutool.json.JSONObject firstContent = content.getJSONObject(0);
                        if (firstContent != null && "text".equals(firstContent.getStr("type"))) {
                            String text = firstContent.getStr("text");
                            if (StringUtils.isNotBlank(text)) {
                                String trimmedText = text.trim();
                                if (trimmedText.startsWith("{") || trimmedText.startsWith("[")) {
                                    try {
                                        return JSONUtil.parseObj(trimmedText);
                                    } catch (Exception e) {
                                        return trimmedText;
                                    }
                                } else if ("true".equals(trimmedText)) {
                                    return true;
                                } else if ("false".equals(trimmedText)) {
                                    return false;
                                } else {
                                    return trimmedText;
                                }
                            }
                        }
                    }
                }
            }
        }
        return null;
    }
}
