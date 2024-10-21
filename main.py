from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# 配置数据库
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///counter.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# 定义计数模型
class Count(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person = db.Column(db.String(1), nullable=False)  # 'z' or 'x'
    date = db.Column(db.String(10), nullable=False)  # 格式 'YYYY-MM-DD'
    count = db.Column(db.Integer, default=0)

    def __init__(self, person, date, count):
        self.person = person
        self.date = date
        self.count = count


# 初始化数据库表
with app.app_context():
    db.create_all()


# 获取今天的计数总数
def get_today_count(person):
    date = datetime.now().strftime("%Y-%m-%d")
    record = Count.query.filter_by(person=person, date=date).first()
    return record.count if record else 0


# 获取所有天数的计数总数
def get_total_count(person):
    total = db.session.query(db.func.sum(Count.count)).filter_by(person=person).scalar()
    return total if total else 0


# 更新计数
def update_counter(person):
    date = datetime.now().strftime("%Y-%m-%d")
    record = Count.query.filter_by(person=person, date=date).first()
    if record:
        record.count += 1
    else:
        new_record = Count(person=person, date=date, count=1)
        db.session.add(new_record)
    db.session.commit()


# 更改某个特定日期的计数
@app.route("/update-count/<person>/<date>", methods=["POST"])
def update_specific_count(person, date):
    if person in ["z", "x"]:
        new_count = request.json.get("count", 0)
        record = Count.query.filter_by(person=person, date=date).first()
        if record:
            record.count = new_count
        else:
            new_record = Count(person=person, date=date, count=new_count)
            db.session.add(new_record)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "person": person,
                    "date": date,
                    "new_count": new_count,
                }
            ),
            200,
        )
    return jsonify({"error": "Invalid person"}), 400


# 更改某个人的总计数，并按比例重新分配给现有的日期
@app.route("/set-total-count/<person>", methods=["POST"])
def set_total_count(person):
    if person in ["z", "x"]:
        new_total = request.json.get("count", 0)
        current_total = get_total_count(person)
        print(new_total, current_total)
        if current_total == 0:
            # 如果当前没有计数，直接把所有计数分配到今天
            date = datetime.now().strftime("%Y-%m-%d")
            record = Count.query.filter_by(person=person, date=date).first()
            if record:
                record.count = new_total
            else:
                new_record = Count(person=person, date=date, count=new_total)
                db.session.add(new_record)
        else:
            # 按比例分配新的总数到现有日期
            records = Count.query.filter_by(person=person).all()
            for record in records:
                ratio = record.count / current_total
                record.count = int(new_total * ratio)
        db.session.commit()
        return (
            jsonify({"status": "success", "person": person, "new_total": new_total}),
            200,
        )
    return jsonify({"error": "Invalid person"}), 400


# 主页显示两个按钮和计数
@app.route("/")
def index():
    # 获取今天和所有天数的计数总数
    today_z = get_today_count("z")
    total_z = get_total_count("z")

    today_x = get_today_count("x")
    total_x = get_total_count("x")

    # 获取所有日期的计数
    z_records = Count.query.filter_by(person="z").all()
    x_records = Count.query.filter_by(person="x").all()

    return render_template(
        "index.html",
        z_records=z_records,
        x_records=x_records,
        today_z=today_z,
        total_z=total_z,
        today_x=today_x,
        total_x=total_x,
    )


# 计数逻辑
@app.route("/count/<person>", methods=["POST"])
def count(person):
    if person in ["z", "x"]:
        update_counter(person)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
