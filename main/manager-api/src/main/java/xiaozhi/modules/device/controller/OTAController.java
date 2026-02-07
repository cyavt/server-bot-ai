package xiaozhi.modules.device.controller;

import java.nio.charset.StandardCharsets;

import org.apache.commons.lang3.StringUtils;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.swagger.v3.oas.annotations.Hidden;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.enums.ParameterIn;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import xiaozhi.common.constant.Constant;
import xiaozhi.modules.device.dto.DeviceReportReqDTO;
import xiaozhi.modules.device.dto.DeviceReportRespDTO;
import xiaozhi.modules.device.entity.DeviceEntity;
import xiaozhi.modules.device.service.DeviceService;
import xiaozhi.modules.sys.service.SysParamsService;

@Tag(name = "Quản lý thiết bị", description = "Các giao diện liên quan đến OTA")
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/ota/")
public class OTAController {
    private final DeviceService deviceService;
    private final SysParamsService sysParamsService;

    @Operation(summary = "Kiểm tra phiên bản OTA và trạng thái kích hoạt thiết bị")
    @PostMapping
    public ResponseEntity<String> checkOTAVersion(
            @RequestBody DeviceReportReqDTO deviceReportReqDTO,
            @Parameter(name = "Device-Id", description = "Định danh duy nhất của thiết bị", required = true, in = ParameterIn.HEADER) @RequestHeader("Device-Id") String deviceId,
            @Parameter(name = "Client-Id", description = "Định danh khách hàng", required = false, in = ParameterIn.HEADER) @RequestHeader(value = "Client-Id", required = false) String clientId) {
        if (StringUtils.isBlank(deviceId)) {
            return createResponse(DeviceReportRespDTO.createError("Device ID is required"));
        }
        if (StringUtils.isBlank(clientId)) {
            clientId = deviceId;
        }
        boolean macAddressValid = isMacAddressValid(deviceId);
        // ID thiết bị và địa chỉ Mac phải nhất quán, và phải có trường application
        if (!macAddressValid) {
            return createResponse(DeviceReportRespDTO.createError("Invalid device ID"));
        }
        return createResponse(deviceService.checkDeviceActive(deviceId, clientId, deviceReportReqDTO));
    }

    @Operation(summary = "Kiểm tra nhanh trạng thái kích hoạt thiết bị")
    @PostMapping("activate")
    public ResponseEntity<String> activateDevice(
            @Parameter(name = "Device-Id", description = "Định danh duy nhất của thiết bị", required = true, in = ParameterIn.HEADER) @RequestHeader("Device-Id") String deviceId,
            @Parameter(name = "Client-Id", description = "Định danh khách hàng", required = false, in = ParameterIn.HEADER) @RequestHeader(value = "Client-Id", required = false) String clientId) {
        if (StringUtils.isBlank(deviceId)) {
            return ResponseEntity.status(202).build();
        }
        DeviceEntity device = deviceService.getDeviceByMacAddress(deviceId);
        if (device == null) {
            return ResponseEntity.status(202).build();
        }
        return ResponseEntity.ok("success");
    }

    @GetMapping
    @Hidden
    public ResponseEntity<String> getOTA() {
        String mqttUdpConfig = sysParamsService.getValue(Constant.SERVER_MQTT_GATEWAY, false);
        if (StringUtils.isBlank(mqttUdpConfig)) {
            return ResponseEntity.ok("Giao diện OTA không bình thường, thiếu địa chỉ mqtt_gateway, vui lòng đăng nhập vào bảng điều khiển thông minh, tìm cấu hình 【server.mqtt_gateway】 trong quản lý tham số");
        }
        String wsUrl = sysParamsService.getValue(Constant.SERVER_WEBSOCKET, true);
        if (StringUtils.isBlank(wsUrl) || wsUrl.equals("null")) {
            return ResponseEntity.ok("Giao diện OTA không bình thường, thiếu địa chỉ websocket, vui lòng đăng nhập vào bảng điều khiển thông minh, tìm cấu hình 【server.websocket】 trong quản lý tham số");
        }
        String otaUrl = sysParamsService.getValue(Constant.SERVER_OTA, true);
        if (StringUtils.isBlank(otaUrl) || otaUrl.equals("null")) {
            return ResponseEntity.ok("Giao diện OTA không bình thường, thiếu địa chỉ ota, vui lòng đăng nhập vào bảng điều khiển thông minh, tìm cấu hình 【server.ota】 trong quản lý tham số");
        }
        return ResponseEntity.ok("Giao diện OTA hoạt động bình thường, số lượng cụm websocket: " + wsUrl.split(";").length);
    }

    @SneakyThrows
    private ResponseEntity<String> createResponse(DeviceReportRespDTO deviceReportRespDTO) {
        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.setSerializationInclusion(JsonInclude.Include.NON_NULL);
        String json = objectMapper.writeValueAsString(deviceReportRespDTO);
        byte[] jsonBytes = json.getBytes(StandardCharsets.UTF_8);
        return ResponseEntity
                .ok()
                .contentType(MediaType.APPLICATION_JSON)
                .contentLength(jsonBytes.length)
                .body(json);
    }

    /**
     * Kiểm tra đơn giản xem địa chỉ mac có hợp lệ không (không nghiêm ngặt)
     * 
     * @param macAddress
     * @return
     */
    private boolean isMacAddressValid(String macAddress) {
        if (StringUtils.isBlank(macAddress)) {
            return false;
        }
        // Địa chỉ MAC thường là 12 chữ số thập lục phân, có thể chứa dấu hai chấm hoặc dấu gạch ngang làm dấu phân cách
        String macPattern = "^([0-9A-Za-z]{2}[:-]){5}([0-9A-Za-z]{2})$";
        return macAddress.matches(macPattern);
    }
}
