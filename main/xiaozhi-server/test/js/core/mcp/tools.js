import { log } from '../../utils/logger.js?v=0205';

// ==========================================
// Logic quản lý công cụ MCP
// ==========================================

// Biến toàn cục
let mcpTools = [];
let mcpEditingIndex = null;
let mcpProperties = [];
let websocket = null; // Sẽ được thiết lập từ bên ngoài

/**
 * Thiết lập instance WebSocket
 * @param {WebSocket} ws - Instance kết nối WebSocket
 */
export function setWebSocket(ws) {
    websocket = ws;
}

/**
 * Khởi tạo công cụ MCP
 */
export async function initMcpTools() {
    // Tải dữ liệu công cụ mặc định
    const defaultMcpTools = await fetch("js/config/default-mcp-tools.json").then(res => res.json());
    const savedTools = localStorage.getItem('mcpTools');
    if (savedTools) {
        try {
            const parsedTools = JSON.parse(savedTools);
            // Hợp nhất công cụ mặc định và công cụ người dùng đã lưu, giữ lại công cụ tùy chỉnh của người dùng
            const defaultToolNames = new Set(defaultMcpTools.map(t => t.name));
            // Thêm công cụ mới không tồn tại trong công cụ mặc định
            parsedTools.forEach(tool => {
                if (!defaultToolNames.has(tool.name)) {
                    defaultMcpTools.push(tool);
                }
            });
            mcpTools = defaultMcpTools;
        } catch (e) {
            log('Tải công cụ MCP thất bại, sử dụng công cụ mặc định', 'warning');
            mcpTools = [...defaultMcpTools];
        }
    } else {
        mcpTools = [...defaultMcpTools];
    }
    renderMcpTools();
    setupMcpEventListeners();
}

/**
 * Render danh sách công cụ
 */
function renderMcpTools() {
    const container = document.getElementById('mcpToolsContainer');
    const countSpan = document.getElementById('mcpToolsCount');
    if (!container) {
        return; // Container not found, skip rendering
    }
    if (countSpan) {
        countSpan.textContent = `${mcpTools.length} công cụ`;
    }
    if (mcpTools.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 30px; color: #999;">Chưa có công cụ, nhấp nút bên dưới để thêm công cụ mới</div>';
        return;
    }
    container.innerHTML = mcpTools.map((tool, index) => {
        const paramCount = tool.inputSchema.properties ? Object.keys(tool.inputSchema.properties).length : 0;
        const requiredCount = tool.inputSchema.required ? tool.inputSchema.required.length : 0;
        const hasMockResponse = tool.mockResponse && Object.keys(tool.mockResponse).length > 0;
        return `
            <div class="mcp-tool-card">
                <div class="mcp-tool-header">
                    <div class="mcp-tool-name">${tool.name}</div>
                    <div class="mcp-tool-actions">
                        <button class="mcp-edit-btn" onclick="window.mcpModule.editMcpTool(${index})">
                            ✏️ Chỉnh sửa
                        </button>
                        <button class="mcp-delete-btn" onclick="window.mcpModule.deleteMcpTool(${index})">
                            🗑️ Xóa
                        </button>
                    </div>
                </div>
                <div class="mcp-tool-description">${tool.description}</div>
                <div class="mcp-tool-info">
                    <div class="mcp-tool-info-row">
                        <span class="mcp-tool-info-label">Số lượng tham số:</span>
                        <span class="mcp-tool-info-value">${paramCount} ${requiredCount > 0 ? `(${requiredCount} bắt buộc)` : ''}</span>
                    </div>
                    <div class="mcp-tool-info-row">
                        <span class="mcp-tool-info-label">Kết quả trả về mô phỏng:</span>
                        <span class="mcp-tool-info-value">${hasMockResponse ? '✅ Đã cấu hình: ' + JSON.stringify(tool.mockResponse) : '⚪ Sử dụng mặc định'}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

/**
 * Render danh sách tham số
 */
function renderMcpProperties() {
    const container = document.getElementById('mcpPropertiesContainer');
    const emptyState = document.getElementById('mcpEmptyState');
    if (!container) {
        return; // Container not found, skip rendering
    }
    if (mcpProperties.length === 0) {
        if (emptyState) {
            emptyState.style.display = 'block';
        }
        container.innerHTML = '';
        return;
    }
    if (emptyState) {
        emptyState.style.display = 'none';
    }
    container.innerHTML = mcpProperties.map((prop, index) => `
        <div class="mcp-property-card" onclick="window.mcpModule.editMcpProperty(${index})">
            <div class="mcp-property-row-label">
                <span class="mcp-property-label">Tên tham số</span>
                <span class="mcp-property-value">${prop.name}${prop.required ? ' <span class="mcp-property-required-badge">[Bắt buộc]</span>' : ''}</span>
            </div>
            <div class="mcp-property-row-label">
                <span class="mcp-property-label">Kiểu dữ liệu</span>
                <span class="mcp-property-value">${getTypeLabel(prop.type)}</span>
            </div>
            <div class="mcp-property-row-label">
                <span class="mcp-property-label">Mô tả</span>
                <span class="mcp-property-value">${prop.description || '-'}</span>
            </div>
            <div class="mcp-property-row-action">
                <button class="mcp-property-delete-btn" onclick="event.stopPropagation(); window.mcpModule.deleteMcpProperty(${index})">Xóa</button>
            </div>
        </div>
    `).join('');
}

/**
 * Lấy nhãn kiểu dữ liệu
 */
function getTypeLabel(type) {
    const typeMap = {
        'string': 'Chuỗi',
        'integer': 'Số nguyên',
        'number': 'Số',
        'boolean': 'Boolean',
        'array': 'Mảng',
        'object': 'Đối tượng'
    };
    return typeMap[type] || type;
}

/**
 * Thêm tham số - Mở hộp thoại chỉnh sửa tham số
 */
function addMcpProperty() {
    openPropertyModal();
}

/**
 * Chỉnh sửa tham số - Mở hộp thoại chỉnh sửa tham số
 */
function editMcpProperty(index) {
    openPropertyModal(index);
}

/**
 * Mở hộp thoại chỉnh sửa tham số
 */
function openPropertyModal(index = null) {
    const form = document.getElementById('mcpPropertyForm');
    const title = document.getElementById('mcpPropertyModalTitle');
    document.getElementById('mcpPropertyIndex').value = index !== null ? index : -1;

    if (index !== null) {
        const prop = mcpProperties[index];
        title.textContent = 'Chỉnh sửa tham số';
        document.getElementById('mcpPropertyName').value = prop.name;
        document.getElementById('mcpPropertyType').value = prop.type || 'string';
        document.getElementById('mcpPropertyMinimum').value = prop.minimum !== undefined ? prop.minimum : '';
        document.getElementById('mcpPropertyMaximum').value = prop.maximum !== undefined ? prop.maximum : '';
        document.getElementById('mcpPropertyDescription').value = prop.description || '';
        document.getElementById('mcpPropertyRequired').checked = prop.required || false;
    } else {
        title.textContent = 'Thêm tham số';
        form.reset();
        document.getElementById('mcpPropertyName').value = `param_${mcpProperties.length + 1}`;
        document.getElementById('mcpPropertyType').value = 'string';
        document.getElementById('mcpPropertyMinimum').value = '';
        document.getElementById('mcpPropertyMaximum').value = '';
        document.getElementById('mcpPropertyDescription').value = '';
        document.getElementById('mcpPropertyRequired').checked = false;
    }

    updatePropertyRangeVisibility();
    document.getElementById('mcpPropertyModal').style.display = 'flex';
}

/**
 * Đóng hộp thoại chỉnh sửa tham số
 */
function closePropertyModal() {
    document.getElementById('mcpPropertyModal').style.display = 'none';
}

/**
 * Cập nhật khả năng hiển thị của hộp nhập phạm vi giá trị
 */
function updatePropertyRangeVisibility() {
    const type = document.getElementById('mcpPropertyType').value;
    const rangeGroup = document.getElementById('mcpPropertyRangeGroup');
    if (type === 'integer' || type === 'number') {
        rangeGroup.style.display = 'block';
    } else {
        rangeGroup.style.display = 'none';
    }
}

/**
 * Xử lý gửi form tham số
 */
function handlePropertySubmit(e) {
    e.preventDefault();
    const index = parseInt(document.getElementById('mcpPropertyIndex').value);
    const name = document.getElementById('mcpPropertyName').value.trim();
    const type = document.getElementById('mcpPropertyType').value;
    const minimum = document.getElementById('mcpPropertyMinimum').value;
    const maximum = document.getElementById('mcpPropertyMaximum').value;
    const description = document.getElementById('mcpPropertyDescription').value.trim();
    const required = document.getElementById('mcpPropertyRequired').checked;

    // Kiểm tra tên trùng lặp
    const isDuplicate = mcpProperties.some((p, i) => i !== index && p.name === name);
    if (isDuplicate) {
        alert('Tên tham số đã tồn tại, vui lòng sử dụng tên khác');
        return;
    }

    const propData = {
        name,
        type,
        description,
        required
    };

    // Thêm giới hạn phạm vi cho kiểu số
    if (type === 'integer' || type === 'number') {
        if (minimum !== '') {
            propData.minimum = parseFloat(minimum);
        }
        if (maximum !== '') {
            propData.maximum = parseFloat(maximum);
        }
    }

    if (index >= 0) {
        mcpProperties[index] = propData;
    } else {
        mcpProperties.push(propData);
    }

    renderMcpProperties();
    closePropertyModal();
}

/**
 * Xóa tham số
 */
function deleteMcpProperty(index) {
    mcpProperties.splice(index, 1);
    renderMcpProperties();
}

/**
 * Thiết lập trình lắng nghe sự kiện
 */
function setupMcpEventListeners() {
    const panel = document.getElementById('mcpToolsPanel');
    const addBtn = document.getElementById('addMcpToolBtn');
    const modal = document.getElementById('mcpToolModal');
    const closeBtn = document.getElementById('closeMcpModalBtn');
    const cancelBtn = document.getElementById('cancelMcpBtn');
    const form = document.getElementById('mcpToolForm');
    const addPropertyBtn = document.getElementById('addMcpPropertyBtn');

    // Các phần tử liên quan đến hộp thoại chỉnh sửa tham số
    const propertyModal = document.getElementById('mcpPropertyModal');
    const closePropertyBtn = document.getElementById('closeMcpPropertyModalBtn');
    const cancelPropertyBtn = document.getElementById('cancelMcpPropertyBtn');
    const propertyForm = document.getElementById('mcpPropertyForm');
    const propertyTypeSelect = document.getElementById('mcpPropertyType');

    // Return early if required elements don't exist (e.g., in test environment)
    if (!panel || !addBtn || !modal || !closeBtn || !cancelBtn || !form || !addPropertyBtn) {
        return;
    }
    addBtn.addEventListener('click', () => openMcpModal());
    closeBtn.addEventListener('click', closeMcpModal);
    cancelBtn.addEventListener('click', closeMcpModal);
    addPropertyBtn.addEventListener('click', addMcpProperty);
    form.addEventListener('submit', handleMcpSubmit);

    // Sự kiện hộp thoại chỉnh sửa tham số
    if (propertyModal && closePropertyBtn && cancelPropertyBtn && propertyForm && propertyTypeSelect) {
        closePropertyBtn.addEventListener('click', closePropertyModal);
        cancelPropertyBtn.addEventListener('click', closePropertyModal);
        propertyForm.addEventListener('submit', handlePropertySubmit);
        propertyTypeSelect.addEventListener('change', updatePropertyRangeVisibility);
    }
}

/**
 * Mở hộp thoại
 */
function openMcpModal(index = null) {
    const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
    if (isConnected) {
        alert('WebSocket đã kết nối, không thể chỉnh sửa công cụ');
        return;
    }
    mcpEditingIndex = index;
    const errorContainer = document.getElementById('mcpErrorContainer');
    errorContainer.innerHTML = '';
    if (index !== null) {
        document.getElementById('mcpModalTitle').textContent = 'Chỉnh sửa công cụ';
        const tool = mcpTools[index];
        document.getElementById('mcpToolName').value = tool.name;
        document.getElementById('mcpToolDescription').value = tool.description;
        document.getElementById('mcpMockResponse').value = tool.mockResponse ? JSON.stringify(tool.mockResponse, null, 2) : '';
        mcpProperties = [];
        const schema = tool.inputSchema;
        if (schema.properties) {
            Object.keys(schema.properties).forEach(key => {
                const prop = schema.properties[key];
                mcpProperties.push({
                    name: key,
                    type: prop.type || 'string',
                    minimum: prop.minimum,
                    maximum: prop.maximum,
                    description: prop.description || '',
                    required: schema.required && schema.required.includes(key)
                });
            });
        }
    } else {
        document.getElementById('mcpModalTitle').textContent = 'Thêm công cụ';
        document.getElementById('mcpToolForm').reset();
        mcpProperties = [];
    }
    renderMcpProperties();
    document.getElementById('mcpToolModal').style.display = 'flex';
}

/**
 * Đóng hộp thoại
 */
function closeMcpModal() {
    document.getElementById('mcpToolModal').style.display = 'none';
    mcpEditingIndex = null;
    document.getElementById('mcpToolForm').reset();
    mcpProperties = [];
    document.getElementById('mcpErrorContainer').innerHTML = '';
}

/**
 * Xử lý gửi form
 */
function handleMcpSubmit(e) {
    e.preventDefault();
    const errorContainer = document.getElementById('mcpErrorContainer');
    errorContainer.innerHTML = '';
    const name = document.getElementById('mcpToolName').value.trim();
    const description = document.getElementById('mcpToolDescription').value.trim();
    const mockResponseText = document.getElementById('mcpMockResponse').value.trim();
    // Kiểm tra tên trùng lặp
    const isDuplicate = mcpTools.some((tool, index) => tool.name === name && index !== mcpEditingIndex);
    if (isDuplicate) {
        showMcpError('Tên công cụ đã tồn tại, vui lòng sử dụng tên khác');
        return;
    }
    // Phân tích kết quả trả về mô phỏng
    let mockResponse = null;
    if (mockResponseText) {
        try {
            mockResponse = JSON.parse(mockResponseText);
        } catch (e) {
            showMcpError('Kết quả trả về mô phỏng không phải định dạng JSON hợp lệ: ' + e.message);
            return;
        }
    }
    // Xây dựng inputSchema
    const inputSchema = { type: "object", properties: {}, required: [] };
    mcpProperties.forEach(prop => {
        const propSchema = { type: prop.type };
        if (prop.description) {
            propSchema.description = prop.description;
        }
        if ((prop.type === 'integer' || prop.type === 'number')) {
            if (prop.minimum !== undefined && prop.minimum !== '') {
                propSchema.minimum = prop.minimum;
            }
            if (prop.maximum !== undefined && prop.maximum !== '') {
                propSchema.maximum = prop.maximum;
            }
        }
        inputSchema.properties[prop.name] = propSchema;
        if (prop.required) {
            inputSchema.required.push(prop.name);
        }
    });
    if (inputSchema.required.length === 0) {
        delete inputSchema.required;
    }
    const tool = { name, description, inputSchema, mockResponse };
    if (mcpEditingIndex !== null) {
        mcpTools[mcpEditingIndex] = tool;
        log(`Đã cập nhật công cụ: ${name}`, 'success');
    } else {
        mcpTools.push(tool);
        log(`Đã thêm công cụ: ${name}`, 'success');
    }
    saveMcpTools();
    renderMcpTools();
    closeMcpModal();
}

/**
 * Hiển thị lỗi
 */
function showMcpError(message) {
    const errorContainer = document.getElementById('mcpErrorContainer');
    errorContainer.innerHTML = `<div class="mcp-error">${message}</div>`;
}

/**
 * Chỉnh sửa công cụ
 */
function editMcpTool(index) {
    openMcpModal(index);
}

/**
 * Xóa công cụ
 */
function deleteMcpTool(index) {
    const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
    if (isConnected) {
        alert('WebSocket đã kết nối, không thể chỉnh sửa công cụ');
        return;
    }
    if (confirm(`Bạn có chắc chắn muốn xóa công cụ "${mcpTools[index].name}" không?`)) {
        const toolName = mcpTools[index].name;
        mcpTools.splice(index, 1);
        saveMcpTools();
        renderMcpTools();
        log(`Đã xóa công cụ: ${toolName}`, 'info');
    }
}

/**
 * Lưu công cụ
 */
function saveMcpTools() {
    localStorage.setItem('mcpTools', JSON.stringify(mcpTools));
}

/**
 * Lấy danh sách công cụ
 */
export function getMcpTools() {
    return mcpTools.map(tool => ({ name: tool.name, description: tool.description, inputSchema: tool.inputSchema }));
}

/**
 * Thực thi gọi công cụ
 */
export async function executeMcpTool(toolName, toolArgs) {
    const tool = mcpTools.find(t => t.name === toolName);
    if (!tool) {
        log(`Không tìm thấy công cụ: ${toolName}`, 'error');
        return { success: false, error: `Công cụ không xác định: ${toolName}` };
    }

    // Xử lý công cụ chụp ảnh
    if (toolName === 'self_camera_take_photo') {
        if (typeof window.takePhoto === 'function') {
            const question = toolArgs && toolArgs.question ? toolArgs.question : 'Mô tả vật phẩm bạn nhìn thấy';
            log(`Đang thực thi chụp ảnh: ${question}`, 'info');
            const result = await window.takePhoto(question);
            return result;
        } else {
            log('Chức năng chụp ảnh không khả dụng', 'warning');
            return { success: false, error: 'Camera chưa khởi động hoặc không hỗ trợ chức năng chụp ảnh' };
        }
    }

    // Nếu có kết quả trả về mô phỏng, sử dụng nó
    if (tool.mockResponse) {
        // Thay thế biến mẫu
        let responseStr = JSON.stringify(tool.mockResponse);
        // Thay thế biến định dạng ${paramName}
        if (toolArgs) {
            Object.keys(toolArgs).forEach(key => {
                const regex = new RegExp(`\\$\\{${key}\\}`, 'g');
                responseStr = responseStr.replace(regex, toolArgs[key]);
            });
        }
        try {
            const response = JSON.parse(responseStr);
            log(`Công cụ ${toolName} thực thi thành công, trả về kết quả mô phỏng: ${responseStr}`, 'success');
            return response;
        } catch (e) {
            log(`Phân tích kết quả trả về mô phỏng thất bại: ${e.message}`, 'error');
            return tool.mockResponse;
        }
    }
    // Không có kết quả trả về mô phỏng, trả về thông báo thành công mặc định
    log(`Công cụ ${toolName} thực thi thành công, trả về kết quả mặc định`, 'success');
    return { success: true, message: `Công cụ ${toolName} thực thi thành công`, tool: toolName, arguments: toolArgs };
}

// Phơi bày phương thức toàn cục để HTML gọi sự kiện nội tuyến
window.mcpModule = { addMcpProperty, editMcpProperty, deleteMcpProperty, editMcpTool, deleteMcpTool };
