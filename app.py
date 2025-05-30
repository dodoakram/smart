from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, timedelta
import calendar
import os
from sqlalchemy import func
import secrets  # لإنشاء التوكن

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # مفتاح سري للجلسات وحماية النماذج

# إعداد حماية CSRF البسيطة
def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

# إضافة دالة csrf_token لاستخدامها في القوالب
app.jinja_env.globals['csrf_token'] = generate_csrf_token

# إعداد قاعدة البيانات
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'attendance.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# تعريف النماذج (Models)
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    absences = db.relationship('Absence', backref='student', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Student {self.name}>'

class Absence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False, default='full')  # 'full' أو 'half'
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    
    def __repr__(self):
        return f'<Absence {self.student_id} on {self.date}>'

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    
    def __repr__(self):
        return f'<Holiday {self.name}>'

# دالة مساعدة للتحقق من العطل
def is_holiday(check_date):
    holidays = Holiday.query.all()
    for holiday in holidays:
        if holiday.start_date <= check_date <= holiday.end_date:
            return True
    return False

# دالة مساعدة للتحقق من أيام العمل (باستثناء العطل وعطلة نهاية الأسبوع)
def is_work_day(check_date):
    # التحقق من أيام الأسبوع (الجمعة والسبت هما عطلة نهاية الأسبوع)
    if check_date.weekday() in [4, 5]:  # 4 = الجمعة، 5 = السبت
        return False
    
    # التحقق من العطل الرسمية
    if is_holiday(check_date):
        return False
    
    return True

# دالة مساعدة لحساب إحصائيات الشهر
def calculate_month_stats(year, month):
    # تحديد اليوم الأول والأخير من الشهر
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # حساب عدد أيام العمل في الشهر
    work_days = 0
    current_date = first_day
    while current_date <= last_day:
        if is_work_day(current_date):
            work_days += 1
        current_date += timedelta(days=1)
    
    # حساب عدد مرات الغياب الكامل والنصفي
    full_absences = Absence.query.filter(
        Absence.date >= first_day,
        Absence.date <= last_day,
        Absence.type == 'full'
    ).count()
    
    half_absences = Absence.query.filter(
        Absence.date >= first_day,
        Absence.date <= last_day,
        Absence.type == 'half'
    ).count()
    
    # حساب إجمالي أيام الغياب (الغياب النصفي يحسب كنصف يوم)
    total_absences = full_absences + (half_absences * 0.5)
    
    # حساب نسبة الحضور
    total_students = Student.query.count()
    if total_students > 0 and work_days > 0:
        total_possible_days = total_students * work_days
        total_absent_days = total_absences
        attendance_rate = ((total_possible_days - total_absent_days) / total_possible_days) * 100
    else:
        attendance_rate = 100
    
    return {
        'work_days': work_days,
        'full_absences': full_absences,
        'half_absences': half_absences,
        'total_absences': total_absences,
        'attendance_rate': attendance_rate
    }

# دالة مساعدة لحساب إحصائيات السنة
def calculate_year_stats(year):
    yearly_stats = {
        'work_days': 0,
        'full_absences': 0,
        'half_absences': 0,
        'total_absences': 0,
        'attendance_rate': 0
    }
    
    for month in range(1, 13):
        month_stats = calculate_month_stats(year, month)
        yearly_stats['work_days'] += month_stats['work_days']
        yearly_stats['full_absences'] += month_stats['full_absences']
        yearly_stats['half_absences'] += month_stats['half_absences']
        yearly_stats['total_absences'] += month_stats['total_absences']
    
    # حساب نسبة الحضور السنوية
    total_students = Student.query.count()
    if total_students > 0 and yearly_stats['work_days'] > 0:
        total_possible_days = total_students * yearly_stats['work_days']
        total_absent_days = yearly_stats['total_absences']
        yearly_stats['attendance_rate'] = ((total_possible_days - total_absent_days) / total_possible_days) * 100
    else:
        yearly_stats['attendance_rate'] = 100
    
    return yearly_stats

# المسارات (Routes)
@app.route('/')
def index():
    today = date.today()
    students = Student.query.all()
    absences_today = Absence.query.filter_by(date=today).all()
    
    # تحديد الطلاب الغائبين اليوم
    absent_students = {absence.student_id: absence.type for absence in absences_today}
    
    return render_template('index.html', 
                          students=students, 
                          absent_students=absent_students,
                          current_date=today,
                          is_holiday=is_holiday(today),
                          is_weekend=(today.weekday() in [4, 5]))

@app.route('/settings')
def settings():
    """صفحة الإعدادات لتعديل إعدادات النظام"""
    # الحصول على جميع الطلاب
    students = Student.query.all()
    # الحصول على جميع العطل
    holidays = Holiday.query.all()
    
    # إحصائيات عامة
    students_count = Student.query.count()
    holidays_count = Holiday.query.count()
    absences_count = Absence.query.count()
    
    return render_template('settings.html', 
                          students=students, 
                          holidays=holidays,
                          students_count=students_count,
                          holidays_count=holidays_count,
                          absences_count=absences_count)

@app.route('/mark_absence', methods=['POST'])
def mark_absence():
    student_id = request.form.get('student_id')
    absence_date = request.form.get('absence_date')
    absence_type = request.form.get('absence_type', 'full')
    
    if not student_id or not absence_date:
        flash('بيانات غير كاملة', 'danger')
        return redirect(url_for('index'))
    
    # تحويل التاريخ من النص إلى كائن تاريخ
    try:
        absence_date = datetime.strptime(absence_date, '%Y-%m-%d').date()
    except ValueError:
        flash('تنسيق تاريخ غير صالح', 'danger')
        return redirect(url_for('index'))
    
    # التحقق من أن التاريخ ليس في المستقبل
    today = date.today()
    if absence_date > today:
        flash('لا يمكن تسجيل الغياب لتاريخ مستقبلي', 'danger')
        return redirect(url_for('index'))
    
    # التحقق من أن اليوم ليس عطلة نهاية الأسبوع (الجمعة أو السبت)
    if absence_date.weekday() in [4, 5]:  # 4 = الجمعة، 5 = السبت
        flash('لا يمكن تسجيل الغياب في أيام عطلة نهاية الأسبوع', 'danger')
        return redirect(url_for('index'))
    
    # التحقق من أن اليوم ليس عطلة رسمية
    if is_holiday(absence_date):
        flash('لا يمكن تسجيل الغياب في أيام العطل الرسمية', 'danger')
        return redirect(url_for('index'))
    
    # التحقق من وجود الطالب
    student = Student.query.get(student_id)
    if not student:
        flash('الطالب غير موجود', 'danger')
        return redirect(url_for('index'))
    
    # التحقق مما إذا كان الطالب مسجل بالفعل كغائب في هذا اليوم
    existing_absence = Absence.query.filter_by(student_id=student_id, date=absence_date).first()
    
    if existing_absence:
        # إذا كان نوع الغياب مختلفًا، قم بتحديثه
        if existing_absence.type != absence_type:
            existing_absence.type = absence_type
            db.session.commit()
            flash('تم تحديث نوع الغياب', 'success')
        else:
            # إذا كان الطالب مسجل بالفعل بنفس نوع الغياب، قم بإلغاء تسجيل الغياب
            db.session.delete(existing_absence)
            db.session.commit()
            flash('تم إلغاء تسجيل الغياب', 'success')
    else:
        # إضافة غياب جديد
        new_absence = Absence(student_id=student_id, date=absence_date, type=absence_type)
        db.session.add(new_absence)
        db.session.commit()
        flash('تم تسجيل الغياب بنجاح', 'success')
    
    return redirect(url_for('index'))

@app.route('/monthly_view')
@app.route('/monthly_view/<int:year>/<int:month>')
def monthly_view(year=None, month=None):
    if year is None or month is None:
        today = date.today()
        year = today.year
        month = today.month
    
    # التحقق من صحة الشهر والسنة
    if month < 1 or month > 12:
        month = date.today().month
    
    # الحصول على عدد الأيام في الشهر
    num_days = calendar.monthrange(year, month)[1]
    first_day = date(year, month, 1)
    
    # إنشاء قائمة بجميع أيام الشهر
    month_days = []
    for day in range(1, num_days + 1):
        current_date = date(year, month, day)
        is_work = is_work_day(current_date)
        month_days.append({
            'date': current_date,
            'is_work_day': is_work,
            'is_holiday': is_holiday(current_date),
            'is_weekend': current_date.weekday() in [4, 5]
        })
    
    # الحصول على جميع الطلاب
    students = Student.query.all()
    
    # الحصول على جميع حالات الغياب في هذا الشهر
    month_start = date(year, month, 1)
    month_end = date(year, month, num_days)
    absences = Absence.query.filter(Absence.date >= month_start, Absence.date <= month_end).all()
    
    # تنظيم حالات الغياب حسب الطالب والتاريخ
    absence_dict = {}
    for absence in absences:
        if absence.student_id not in absence_dict:
            absence_dict[absence.student_id] = {}
        absence_dict[absence.student_id][absence.date.day] = absence.type
    
    # الحصول على الشهر السابق والتالي للتنقل
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1
    
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year += 1
    
    # أسماء الأشهر بالعربية
    arabic_months = [
        "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    
    return render_template('monthly_view.html',
                          year=year,
                          month=month,
                          month_name=arabic_months[month-1],
                          month_days=month_days,
                          students=students,
                          absences=absence_dict,
                          prev_month=prev_month,
                          prev_year=prev_year,
                          next_month=next_month,
                          next_year=next_year,
                          current_date=date.today())

@app.route('/toggle_absence/<int:student_id>/<string:absence_date>/<string:absence_type>', methods=['POST'])
def toggle_absence(student_id, absence_date, absence_type):
    # تحويل التاريخ من النص إلى كائن تاريخ
    try:
        absence_date = datetime.strptime(absence_date, '%Y-%m-%d').date()
    except ValueError:
        flash('تنسيق تاريخ غير صالح', 'danger')
        return redirect(url_for('monthly_view'))
    
    # التحقق من أن التاريخ ليس في المستقبل
    today = date.today()
    if absence_date > today:
        flash('لا يمكن تسجيل الغياب لتاريخ مستقبلي', 'danger')
        return redirect(url_for('monthly_view', year=absence_date.year, month=absence_date.month))
    
    # التحقق من أن اليوم ليس عطلة نهاية الأسبوع (الجمعة أو السبت)
    if absence_date.weekday() in [4, 5]:  # 4 = الجمعة، 5 = السبت
        flash('لا يمكن تسجيل الغياب في أيام عطلة نهاية الأسبوع', 'danger')
        return redirect(url_for('monthly_view', year=absence_date.year, month=absence_date.month))
    
    # التحقق من أن اليوم ليس عطلة رسمية
    if is_holiday(absence_date):
        flash('لا يمكن تسجيل الغياب في أيام العطل الرسمية', 'danger')
        return redirect(url_for('monthly_view', year=absence_date.year, month=absence_date.month))
    
    # التحقق من وجود الطالب
    student = Student.query.get(student_id)
    if not student:
        flash('الطالب غير موجود', 'danger')
        return redirect(url_for('monthly_view', year=absence_date.year, month=absence_date.month))
    
    # التحقق مما إذا كان الطالب مسجل بالفعل كغائب في هذا اليوم
    existing_absence = Absence.query.filter_by(student_id=student_id, date=absence_date).first()
    
    if existing_absence:
        # إذا كان نوع الغياب مختلفًا، قم بتحديثه
        if existing_absence.type != absence_type:
            existing_absence.type = absence_type
            db.session.commit()
            flash('تم تحديث نوع الغياب', 'success')
        else:
            # إذا كان الطالب مسجل بالفعل بنفس نوع الغياب، قم بإلغاء تسجيل الغياب
            db.session.delete(existing_absence)
            db.session.commit()
            flash('تم إلغاء تسجيل الغياب', 'success')
    else:
        # إضافة غياب جديد
        new_absence = Absence(student_id=student_id, date=absence_date, type=absence_type)
        db.session.add(new_absence)
        db.session.commit()
        flash('تم تسجيل الغياب بنجاح', 'success')
    
    return redirect(url_for('monthly_view', year=absence_date.year, month=absence_date.month))

@app.route('/monthly_statistics')
@app.route('/monthly_statistics/<int:year>')
def monthly_statistics(year=None):
    if year is None:
        year = date.today().year
    
    # أسماء الأشهر بالعربية
    arabic_months = [
        "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
        "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
    ]
    
    # حساب إحصائيات كل شهر
    monthly_stats = {}
    for month in range(1, 13):
        monthly_stats[month] = calculate_month_stats(year, month)
    
    # حساب إحصائيات السنة
    yearly_stats = calculate_year_stats(year)
    
    # إنشاء قائمة بأرقام وأسماء الأشهر
    months = [(i, arabic_months[i-1]) for i in range(1, 13)]
    
    return render_template('monthly_statistics.html',
                          current_year=year,
                          months=months,
                          monthly_stats=monthly_stats,
                          yearly_stats=yearly_stats,
                          current_date=date.today())

@app.route('/statistics')
def statistics():
    # حساب عدد الطلاب
    students_count = Student.query.count()
    
    # حساب عدد العطل
    holidays_count = Holiday.query.count()
    
    # حساب إجمالي أيام الغياب
    absent_count = Absence.query.filter_by(type='full').count() + (Absence.query.filter_by(type='half').count() * 0.5)
    
    # حساب نسبة الحضور
    current_year = date.today().year
    yearly_stats = calculate_year_stats(current_year)
    present_percentage = round(yearly_stats['attendance_rate'], 2)
    
    return render_template('statistics.html',
                          students_count=students_count,
                          holidays_count=holidays_count,
                          absent_count=absent_count,
                          present_percentage=present_percentage,
                          current_date=date.today())

@app.route('/manage_students')
def manage_students():
    students = Student.query.all()
    return render_template('students.html', students=students, current_date=date.today())

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get('name')
    
    if not name:
        flash('يرجى إدخال اسم الطالب', 'danger')
        return redirect(url_for('manage_students'))
    
    new_student = Student(name=name)
    db.session.add(new_student)
    db.session.commit()
    
    flash('تمت إضافة الطالب بنجاح', 'success')
    return redirect(url_for('manage_students'))

@app.route('/update_student/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    data = request.get_json()
    
    student = Student.query.get_or_404(student_id)
    student.name = data.get('name', student.name)
    
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    
    db.session.delete(student)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/add_holiday', methods=['POST'])
def add_holiday():
    name = request.form.get('name')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    if not name or not start_date or not end_date:
        flash('يرجى إدخال جميع البيانات المطلوبة', 'danger')
        return redirect(url_for('index'))
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        flash('تنسيق تاريخ غير صالح', 'danger')
        return redirect(url_for('index'))
    
    if start_date > end_date:
        flash('تاريخ البداية يجب أن يكون قبل تاريخ النهاية', 'danger')
        return redirect(url_for('index'))
    
    # التحقق من تداخل العطل
    overlapping_holidays = Holiday.query.filter(
        ((Holiday.start_date <= start_date) & (Holiday.end_date >= start_date)) |
        ((Holiday.start_date <= end_date) & (Holiday.end_date >= end_date)) |
        ((Holiday.start_date >= start_date) & (Holiday.end_date <= end_date))
    ).all()
    
    if overlapping_holidays:
        flash('هناك عطلة أخرى في نفس الفترة الزمنية', 'warning')
        return redirect(url_for('index'))
    
    new_holiday = Holiday(name=name, start_date=start_date, end_date=end_date)
    db.session.add(new_holiday)
    db.session.commit()
    
    flash('تمت إضافة العطلة بنجاح', 'success')
    return redirect(url_for('holidays'))

@app.route('/update_holiday/<int:holiday_id>', methods=['PUT'])
def update_holiday(holiday_id):
    data = request.get_json()
    
    holiday = Holiday.query.get_or_404(holiday_id)
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'اسم العطلة مطلوب'})
    
    holiday.name = data.get('name')
    
    try:
        if 'start_date' in data:
            new_start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        else:
            new_start_date = holiday.start_date
            
        if 'end_date' in data:
            new_end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        else:
            new_end_date = holiday.end_date
    except ValueError:
        return jsonify({'success': False, 'message': 'تنسيق تاريخ غير صالح'})
    
    if new_start_date > new_end_date:
        return jsonify({'success': False, 'message': 'تاريخ البداية يجب أن يكون قبل تاريخ النهاية'})
    
    # التحقق من تداخل العطل (باستثناء العطلة الحالية)
    overlapping_holidays = Holiday.query.filter(
        Holiday.id != holiday_id,
        (
            ((Holiday.start_date <= new_start_date) & (Holiday.end_date >= new_start_date)) |
            ((Holiday.start_date <= new_end_date) & (Holiday.end_date >= new_end_date)) |
            ((Holiday.start_date >= new_start_date) & (Holiday.end_date <= new_end_date))
        )
    ).all()
    
    if overlapping_holidays:
        return jsonify({'success': False, 'message': 'هناك عطلة أخرى في نفس الفترة الزمنية'})
    
    holiday.start_date = new_start_date
    holiday.end_date = new_end_date
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'holiday': {
            'id': holiday.id,
            'name': holiday.name,
            'start_date': holiday.start_date.strftime('%Y-%m-%d'),
            'end_date': holiday.end_date.strftime('%Y-%m-%d'),
            'duration': (holiday.end_date - holiday.start_date).days + 1
        }
    })

@app.route('/delete_holiday/<int:holiday_id>', methods=['DELETE'])
def delete_holiday(holiday_id):
    holiday = Holiday.query.get_or_404(holiday_id)
    
    # التحقق مما إذا كانت هناك غيابات مسجلة في أيام هذه العطلة
    absences_in_holiday = Absence.query.filter(
        Absence.date >= holiday.start_date,
        Absence.date <= holiday.end_date
    ).count()
    
    if absences_in_holiday > 0:
        return jsonify({
            'success': False, 
            'message': 'لا يمكن حذف هذه العطلة لأن هناك غيابات مسجلة خلالها'
        })
    
    db.session.delete(holiday)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/holidays')
def holidays():
    all_holidays = Holiday.query.order_by(Holiday.start_date.desc()).all()
    return render_template('holidays.html', holidays=all_holidays, current_date=date.today())

# إنشاء قاعدة البيانات عند تشغيل التطبيق
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)