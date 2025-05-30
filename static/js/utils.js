/**
 * وظائف مساعدة لنظام إدارة الحضور والغياب
 */

/**
 * الحصول على قيمة ملف تعريف الارتباط (Cookie) بالاسم المحدد
 * @param {string} name - اسم ملف تعريف الارتباط
 * @returns {string} قيمة ملف تعريف الارتباط أو سلسلة فارغة إذا لم يتم العثور عليه
 */
function getCookie(name) {
    // للتعامل مع csrf_token في نماذج HTML
    if (name === 'csrf_token') {
        // البحث عن عنصر input مخفي بالاسم csrf_token
        const tokenElement = document.querySelector('input[name="csrf_token"]');
        if (tokenElement) {
            return tokenElement.value;
        }
        
        // البحث عن عنصر meta بالاسم csrf-token
        const metaElement = document.querySelector('meta[name="csrf-token"]');
        if (metaElement) {
            return metaElement.getAttribute('content');
        }
    }
    
    // البحث في ملفات تعريف الارتباط
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // هل يبدأ هذا الكوكي بالاسم الذي نبحث عنه؟
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * إعداد أزرار التفاعل مع الطلاب (تعديل وحذف)
 */
function setupStudentButtons() {
    // معالجة أزرار تعديل الطالب
    document.querySelectorAll('.edit-student').forEach(btn => {
        btn.addEventListener('click', function() {
            const studentId = this.dataset.id;
            const studentRow = this.closest('tr');
            const studentName = studentRow.querySelector('.student-name').textContent;
            
            // إنشاء نموذج تعديل مباشر في الصف
            const originalContent = studentRow.innerHTML;
            studentRow.innerHTML = `
                <td colspan="4">
                    <form id="edit-student-form-${studentId}" class="d-flex align-items-center">
                        <input type="text" class="form-control me-2" id="edit-student-name-${studentId}" value="${studentName}" required>
                        <button type="submit" class="btn btn-success me-2">
                            <i class="fas fa-check"></i> حفظ
                        </button>
                        <button type="button" class="btn btn-secondary cancel-edit">
                            <i class="fas fa-times"></i> إلغاء
                        </button>
                    </form>
                </td>
            `;
            
            // معالجة إلغاء التعديل
            studentRow.querySelector('.cancel-edit').addEventListener('click', function() {
                studentRow.innerHTML = originalContent;
                setupStudentButtons(); // إعادة إعداد الأزرار بعد الإلغاء
            });
            
            // معالجة إرسال نموذج التعديل
            document.getElementById(`edit-student-form-${studentId}`).addEventListener('submit', function(e) {
                e.preventDefault();
                
                const newName = document.getElementById(`edit-student-name-${studentId}`).value;
                
                if (!newName.trim()) {
                    showAlert('يرجى إدخال اسم الطالب', 'danger');
                    return;
                }
                
                fetch(`/update_student/${studentId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrf_token')
                    },
                    body: JSON.stringify({ name: newName })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // تحديث اسم الطالب في الصف
                        studentRow.innerHTML = originalContent;
                        studentRow.querySelector('.student-name').textContent = newName;
                        setupStudentButtons(); // إعادة إعداد الأزرار بعد التحديث
                        showAlert('تم تحديث بيانات الطالب بنجاح', 'success');
                    } else {
                        showAlert('حدث خطأ أثناء تحديث بيانات الطالب', 'danger');
                        studentRow.innerHTML = originalContent;
                        setupStudentButtons(); // إعادة إعداد الأزرار بعد الفشل
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showAlert('حدث خطأ في الاتصال بالخادم', 'danger');
                    studentRow.innerHTML = originalContent;
                    setupStudentButtons(); // إعادة إعداد الأزرار بعد الفشل
                });
            });
        });
    });
    
    // معالجة أزرار حذف الطالب
    document.querySelectorAll('.delete-student').forEach(btn => {
        btn.addEventListener('click', function() {
            const studentId = this.dataset.id;
            const studentName = this.dataset.name;
            
            if (confirm(`هل أنت متأكد من حذف الطالب: ${studentName}؟`)) {
                fetch(`/delete_student/${studentId}`, {
                    method: 'DELETE',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrf_token')
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // إزالة صف الطالب مع تأثير التلاشي
                        const row = this.closest('tr');
                        row.classList.add('fade-out');
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
}

/**
 * عرض رسالة تنبيه
 * @param {string} message - نص الرسالة
 * @param {string} type - نوع التنبيه (success, danger, warning, info)
 */
function showAlert(message, type = 'info') {
    // إنشاء عنصر التنبيه
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.role = 'alert';
    
    // إضافة نص الرسالة وزر الإغلاق
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="إغلاق"></button>
    `;
    
    // إضافة التنبيه إلى الصفحة
    const alertContainer = document.querySelector('.alert-container');
    if (alertContainer) {
        alertContainer.appendChild(alertDiv);
    } else {
        // إذا لم يكن هناك حاوية للتنبيهات، أضف التنبيه في أعلى المحتوى الرئيسي
        const mainContent = document.querySelector('main');
        if (mainContent) {
            const newAlertContainer = document.createElement('div');
            newAlertContainer.className = 'alert-container mt-3';
            newAlertContainer.appendChild(alertDiv);
            mainContent.prepend(newAlertContainer);
        }
    }
    
    // إزالة التنبيه تلقائيًا بعد 5 ثوانٍ
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 300);
        }
    }, 5000);
}
