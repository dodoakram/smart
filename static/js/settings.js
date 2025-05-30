/**
 * ملف الإعدادات المشتركة لنظام إدارة الحضور والغياب
 */

// تهيئة المتغيرات العامة
let currentDate = new Date();

// تهيئة الصفحة عند تحميلها
document.addEventListener('DOMContentLoaded', function() {
    // تفعيل التلميحات
    initTooltips();
    
    // تفعيل النوافذ المنبثقة
    initModals();
    
    // تفعيل التنبيهات التلقائية
    initAlerts();
    
    // تفعيل أزرار الطلاب
    setupStudentButtons();
    
    // إضافة أنماط CSS للتأثيرات
    if (!document.getElementById('student-styles')) {
        const style = document.createElement('style');
        style.id = 'student-styles';
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

/**
 * تهيئة التلميحات
 */
function initTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * تهيئة النوافذ المنبثقة
 */
function initModals() {
    // تهيئة نماذج إضافة الطالب
    const addStudentModal = document.getElementById('addStudentModal');
    if (addStudentModal) {
        addStudentModal.addEventListener('shown.bs.modal', function () {
            document.getElementById('studentName').focus();
        });
    }
    
    // تهيئة نماذج إضافة العطلة
    const addHolidayModal = document.getElementById('addHolidayModal');
    if (addHolidayModal) {
        addHolidayModal.addEventListener('shown.bs.modal', function () {
            document.getElementById('holidayName').focus();
        });
    }
}

/**
 * تهيئة التنبيهات
 */
function initAlerts() {
    // إغلاق رسائل التنبيه تلقائيًا بعد 5 ثوانٍ
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            if (typeof bootstrap !== 'undefined') {
                var bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.display = 'none';
            }
        });
    }, 5000);
}

/**
 * تنسيق التاريخ بالصيغة المحلية
 * @param {Date|string} date - التاريخ المراد تنسيقه
 * @returns {string} التاريخ المنسق
 */
function formatDate(date) {
    if (typeof date === 'string') {
        date = new Date(date);
    }
    
    return date.toLocaleDateString('ar-SA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * تحويل التاريخ إلى صيغة YYYY-MM-DD
 * @param {Date} date - التاريخ المراد تحويله
 * @returns {string} التاريخ بصيغة YYYY-MM-DD
 */
function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    return `${year}-${month}-${day}`;
}

// دالة لإعداد أزرار التعديل والحذف
function setupStudentButtons() {
    // إزالة أي مستمعي أحداث سابقين
    document.querySelectorAll('.edit-student, .delete-student').forEach(btn => {
        btn.replaceWith(btn.cloneNode(true));
    });

    // معالجة حذف الطالب
    document.querySelectorAll('.delete-student').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const studentId = this.dataset.id;
            const studentName = this.dataset.name;
            
            if (confirm(`هل أنت متأكد من حذف الطالب: ${studentName}؟`)) {
                fetch(`/delete_student/${studentId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // إزالة صف الطالب مع تأثير التلاشي
                        const row = this.closest('tr');
                        row.style.animation = 'fadeOut 0.3s';
                        setTimeout(() => row.remove(), 300);
                        
                        // إظهار رسالة نجاح
                        showAlert('تم حذف الطالب بنجاح', 'success');
                    } else {
                        showAlert('حدث خطأ أثناء حذف الطالب', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('حدث خطأ في الاتصال بالخادم', 'danger');
                });
            }
        });
    });

    // معالجة تعديل الطالب
    document.querySelectorAll('.edit-student').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const studentId = this.dataset.id;
            const row = this.closest('tr');
            const studentNameCell = row.querySelector('.student-name');
            const currentName = studentNameCell.textContent.trim();
            
            const newName = prompt('أدخل الاسم الجديد للطالب:', currentName);
            
            if (newName && newName !== currentName) {
                fetch(`/update_student/${studentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify({ name: newName })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // تحديث الاسم في الجدول
                        studentNameCell.textContent = newName;
                        // تحديث زر الحذف بالاسم الجديد
                        const deleteBtn = row.querySelector('.delete-student');
                        if (deleteBtn) {
                            deleteBtn.dataset.name = newName;
                        }
                        showAlert('تم تحديث اسم الطالب بنجاح', 'success');
                    } else {
                        showAlert('حدث خطأ أثناء تحديث اسم الطالب', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('حدث خطأ في الاتصال بالخادم', 'danger');
                });
            }
        });
    });
}

// دالة مساعدة للحصول على قيمة الكوكي
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

// دالة لعرض رسائل التنبيه
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // إضافة الرسالة في أعلى الصفحة
    const container = document.querySelector('.container-fluid') || document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // إزالة الرسالة بعد 5 ثواني
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    }
}
