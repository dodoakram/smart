/**
 * وظائف إدارة العطل الرسمية
 */

document.addEventListener('DOMContentLoaded', function() {
    // تهيئة متغيرات JavaScript
    let currentHolidayId = null;

    // تهيئة نموذج التعديل عند النقر على زر التعديل
    document.querySelectorAll('.edit-holiday').forEach(btn => {
        btn.addEventListener('click', function() {
            currentHolidayId = this.dataset.id;
            document.getElementById('editHolidayId').value = currentHolidayId;
            document.getElementById('editHolidayName').value = this.dataset.name;
            document.getElementById('editHolidayStart').value = this.dataset.start;
            document.getElementById('editHolidayEnd').value = this.dataset.end;
            
            // فتح النافذة المنبثقة
            const modal = new bootstrap.Modal(document.getElementById('editHolidayModal'));
            modal.show();
        });
    });

    // معالجة حذف العطلة
    document.querySelectorAll('.delete-holiday').forEach(btn => {
        btn.addEventListener('click', function() {
            const holidayId = this.dataset.id;
            const holidayName = this.dataset.name;
            
            if (confirm(`هل أنت متأكد من حذف العطلة: ${holidayName}؟`)) {
                fetch(`/delete_holiday/${holidayId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrf_token')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // إزالة صف العطلة مع تأثير التلاشي
                        const row = this.closest('tr');
                        row.classList.add('fade-out');
                        setTimeout(() => row.remove(), 300);
                        
                        // إظهار رسالة نجاح
                        showAlert('تم حذف العطلة بنجاح', 'success');
                    } else {
                        showAlert(data.message || 'حدث خطأ أثناء حذف العطلة', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('حدث خطأ في الاتصال بالخادم', 'danger');
                });
            }
        });
    });

    // معالجة إرسال نموذج التعديل
    document.getElementById('editHolidayForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('editHolidayName').value,
            start_date: document.getElementById('editHolidayStart').value,
            end_date: document.getElementById('editHolidayEnd').value
        };
        
        fetch(`/update_holiday/${currentHolidayId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrf_token')
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // إغلاق النافذة المنبثقة
                const modal = bootstrap.Modal.getInstance(document.getElementById('editHolidayModal'));
                modal.hide();
                
                // تحديث الصفحة لعرض التغييرات
                location.reload();
            } else {
                showAlert(data.message || 'حدث خطأ أثناء تحديث العطلة', 'danger');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('حدث خطأ في الاتصال بالخادم', 'danger');
        });
    });

    // تهيئة حقول التاريخ عند فتح نموذج إضافة عطلة جديدة
    const addHolidayModal = document.getElementById('addHolidayModal');
    if (addHolidayModal) {
        addHolidayModal.addEventListener('show.bs.modal', function() {
            // تعيين تاريخ اليوم كقيمة افتراضية لتاريخ البداية والنهاية
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('startDate').value = today;
            document.getElementById('endDate').value = today;
        });
    }

    // إضافة التحقق من صحة التواريخ
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    
    if (startDateInput && endDateInput) {
        // التأكد من أن تاريخ النهاية لا يسبق تاريخ البداية
        endDateInput.addEventListener('change', function() {
            if (this.value < startDateInput.value) {
                showAlert('تاريخ النهاية لا يمكن أن يكون قبل تاريخ البداية', 'warning');
                this.value = startDateInput.value;
            }
        });
        
        startDateInput.addEventListener('change', function() {
            if (this.value > endDateInput.value) {
                endDateInput.value = this.value;
            }
        });
    }

    // نفس الشيء لنموذج التعديل
    const editStartDateInput = document.getElementById('editHolidayStart');
    const editEndDateInput = document.getElementById('editHolidayEnd');
    
    if (editStartDateInput && editEndDateInput) {
        editEndDateInput.addEventListener('change', function() {
            if (this.value < editStartDateInput.value) {
                showAlert('تاريخ النهاية لا يمكن أن يكون قبل تاريخ البداية', 'warning');
                this.value = editStartDateInput.value;
            }
        });
        
        editStartDateInput.addEventListener('change', function() {
            if (this.value > editEndDateInput.value) {
                editEndDateInput.value = this.value;
            }
        });
    }

    // إضافة أنماط CSS للتأثيرات
    if (!document.getElementById('holiday-styles')) {
        const style = document.createElement('style');
        style.id = 'holiday-styles';
        style.textContent = `
            @keyframes fadeOut {
                from { opacity: 1; transform: translateY(0); }
                to { opacity: 0; transform: translateY(-10px); }
            }
            tr.fade-out {
                animation: fadeOut 0.3s forwards;
            }
            .action-buttons {
                white-space: nowrap;
            }
            .action-buttons .btn {
                margin: 0 2px;
            }
        `;
        document.head.appendChild(style);
    }
});

// استخدام دالة getCookie من ملف utils.js
// في حالة عدم وجود الدالة، نضيفها هنا كنسخة احتياطية
if (typeof getCookie !== 'function') {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// استخدام دالة showAlert من ملف utils.js
// في حالة عدم وجود الدالة، نضيفها هنا كنسخة احتياطية
if (typeof showAlert !== 'function') {
    function showAlert(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="إغلاق"></button>
        `;
        
        const alertContainer = document.querySelector('.alert-container');
        if (alertContainer) {
            alertContainer.appendChild(alertDiv);
        } else {
            const mainContent = document.querySelector('main');
            if (mainContent) {
                const newAlertContainer = document.createElement('div');
                newAlertContainer.className = 'alert-container mt-3';
                newAlertContainer.appendChild(alertDiv);
                mainContent.prepend(newAlertContainer);
            }
        }
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => alertDiv.remove(), 300);
            }
        }, 5000);
    }
}
