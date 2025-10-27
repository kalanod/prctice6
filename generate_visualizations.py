import csv
import json
import os
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean

out_dir = "visualizations"
os.makedirs(out_dir, exist_ok=True)

plotly_cdn = "https://cdn.plot.ly/plotly-2.27.0.min.js"

def write_plotly(name, traces, layout):
    html = f"""<!DOCTYPE html><html><head><meta charset='utf-8'><title>{layout.get('title','Chart')}</title></head><body><div id='chart' style='width:100%;height:100vh;'></div><script src='{plotly_cdn}'></script><script>Plotly.newPlot('chart', {json.dumps(traces)}, {json.dumps(layout)}, {{responsive:true}});</script></body></html>"""
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        f.write(html)

def write_svg_bar(name, title, labels, values, y_title):
    width, height, margin = 900, 520, 70
    inner_w = width - 2 * margin
    inner_h = height - 2 * margin
    max_val = max(values) if values else 1
    step = inner_w / max(len(values), 1)
    bar_w = step * 0.6
    parts = ["<?xml version='1.0' encoding='UTF-8'?>", f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>", f"<rect width='{width}' height='{height}' fill='white'/>", f"<text x='{width/2}' y='{margin/2}' text-anchor='middle' font-size='20' font-family='sans-serif'>{title}</text>", f"<text x='{margin/3}' y='{margin-20}' text-anchor='start' font-size='14' font-family='sans-serif' transform='rotate(-90 {margin/3} {margin-20})'>{y_title}</text>", f"<line x1='{margin}' y1='{height-margin}' x2='{width-margin}' y2='{height-margin}' stroke='black'/>", f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{height-margin}' stroke='black'/>"]
    for i,val in enumerate(values):
        x = margin + i * step + (step - bar_w) / 2
        bar_h = 0 if max_val == 0 else (val / max_val) * inner_h
        y = height - margin - bar_h
        parts.append(f"<rect x='{x}' y='{y}' width='{bar_w}' height='{bar_h}' fill='#4f81bd'/>")
        parts.append(f"<text x='{x + bar_w / 2}' y='{y - 5}' text-anchor='middle' font-size='12' font-family='sans-serif'>{round(val,2)}</text>")
        parts.append(f"<text x='{x + bar_w / 2}' y='{height - margin + 40}' font-size='12' font-family='sans-serif' text-anchor='end' transform='rotate(-45 {x + bar_w / 2} {height - margin + 40})'>{labels[i]}</text>")
    for j in range(6):
        val = max_val * j / 5
        y = height - margin - (0 if max_val == 0 else val / max_val * inner_h)
        parts.append(f"<line x1='{margin-5}' y1='{y}' x2='{margin}' y2='{y}' stroke='black'/>")
        parts.append(f"<text x='{margin-10}' y='{y+5}' text-anchor='end' font-size='12' font-family='sans-serif'>{round(val,2)}</text>")
    parts.append("</svg>")
    with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
        f.write("".join(parts))

# Electric vehicle
make_counts = Counter()
scatter_by_type = defaultdict(list)
with open("data/Electric_Vehicle_Population_Data.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        make = row.get("Make", "").strip()
        if make:
            make_counts[make] += 1
        try:
            rng = float(row.get("Electric Range", ""))
            msrp = float(row.get("Base MSRP", ""))
        except ValueError:
            continue
        kind = row.get("Electric Vehicle Type", "Unknown") or "Unknown"
        scatter_by_type[kind].append((rng, msrp, row.get("Model", "")))

top_makes = make_counts.most_common(10)
write_svg_bar("electric_make_counts.svg", "Top Electric Vehicle Makes", [m for m,_ in top_makes], [c for _,c in top_makes], "Registrations")
scatter_traces = []
for kind, entries in scatter_by_type.items():
    xs = [r for r,_,_ in entries][:1200]
    ys = [p for _,p,_ in entries][:1200]
    texts = [t for _,_,t in entries][:1200]
    scatter_traces.append({"type":"scatter","mode":"markers","name":kind,"x":xs,"y":ys,"text":texts,"hovertemplate":"Range: %{x}<br>MSRP: %{y}<br>Model: %{text}<extra></extra>","marker":{"size":8}})
write_plotly("electric_range_price_scatter.html", scatter_traces, {"title":"Range vs MSRP by Electric Vehicle Type","xaxis":{"title":"Electric Range (miles)"},"yaxis":{"title":"Base MSRP (USD)"}})

# Restaurant inspections
grade_counts = Counter()
month_scores = defaultdict(list)
with open("data/Restaurant_and_Market_Health_Inspections.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        grade = row.get("grade", "").strip()
        if grade:
            grade_counts[grade] += 1
        score_txt = row.get("score", "").strip()
        date_txt = row.get("activity_date", "").strip()
        if not score_txt or not date_txt:
            continue
        try:
            score = float(score_txt)
        except ValueError:
            continue
        for fmt in ("%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_txt, fmt)
                break
            except ValueError:
                dt = None
        if dt is None:
            continue
        month = dt.strftime("%Y-%m")
        month_scores[month].append(score)

grade_order = [item[0] for item in grade_counts.most_common()]
write_svg_bar("restaurant_grade_counts.svg", "Inspection Grade Counts", grade_order, [grade_counts[g] for g in grade_order], "Inspections")
months_sorted = sorted(month_scores)
line_trace = [{"type":"scatter","mode":"lines+markers","name":"Average Score","x":months_sorted,"y":[round(mean(month_scores[m]),2) for m in months_sorted],"hovertemplate":"%{x}<br>Score: %{y}<extra></extra>"}]
write_plotly("restaurant_scores_by_month.html", line_trace, {"title":"Average Inspection Score by Month","xaxis":{"title":"Month"},"yaxis":{"title":"Average Score"}})

# Employee salaries
base_by_dept = defaultdict(list)
scatter_points = []
with open("data/Employee_Salaries_-_2023.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        dept = row.get("Department_Name", "").strip()
        base_txt = row.get("Base_Salary", "").strip()
        over_txt = row.get("Overtime_Pay", "").strip()
        try:
            base = float(base_txt)
        except ValueError:
            continue
        base_by_dept[dept].append(base)
        try:
            overtime = float(over_txt) if over_txt else 0.0
        except ValueError:
            overtime = 0.0
        scatter_points.append((base, overtime, dept, row.get("Division", "")))

top_depts = sorted(base_by_dept.items(), key=lambda kv: len(kv[1]), reverse=True)[:10]
write_svg_bar("employee_avg_salary.svg", "Average Base Salary by Department", [d for d,_ in top_depts], [round(mean(vals),2) for _,vals in top_depts], "Average Salary (USD)")
points = scatter_points[:1500]
scatter = [{"type":"scatter","mode":"markers","name":"Employees","x":[p[0] for p in points],"y":[p[1] for p in points],"text":[p[2] for p in points],"hovertemplate":"Base: %{x}<br>Overtime: %{y}<br>Dept: %{text}<extra></extra>","marker":{"size":7}}]
write_plotly("employee_salary_overtime.html", scatter, {"title":"Base Salary vs Overtime","xaxis":{"title":"Base Salary"},"yaxis":{"title":"Overtime Pay"}})

# Backloggd games
genre_counts = Counter()
release_points = defaultdict(lambda: {"x":[],"y":[],"text":[]})
with open("data/backloggd_games.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        genres = [g.strip() for g in row.get("Genres", "").split(",") if g.strip()]
        for g in genres:
            genre_counts[g] += 1
        date_txt = row.get("Release_Date", "").strip()
        rating_txt = row.get("Rating", "").strip()
        if not date_txt or not rating_txt:
            continue
        try:
            rating = float(rating_txt)
        except ValueError:
            continue
        try:
            dt = datetime.strptime(date_txt, "%b %d, %Y")
            year = dt.year
        except ValueError:
            parts = date_txt.split()
            if parts and parts[-1].isdigit():
                year = int(parts[-1])
            else:
                continue
        release_points[row.get("Platforms", "Unknown")] = release_points[row.get("Platforms", "Unknown")]
        release_points[row.get("Platforms", "Unknown")]["x"].append(year)
        release_points[row.get("Platforms", "Unknown")]["y"].append(rating)
        release_points[row.get("Platforms", "Unknown")]["text"].append(row.get("Title", ""))

top_genres = genre_counts.most_common(10)
write_svg_bar("games_top_genres.svg", "Top Game Genres", [g for g,_ in top_genres], [c for _,c in top_genres], "Games")
platform_traces = []
for platform, data in sorted(release_points.items(), key=lambda kv: len(kv[1]["x"]), reverse=True)[:6]:
    platform_traces.append({"type":"scatter","mode":"markers","name":platform[:20] or "Unknown","x":data["x"],"y":data["y"],"text":data["text"],"hovertemplate":"Year: %{x}<br>Rating: %{y}<br>%{text}<extra></extra>","marker":{"size":7}})
write_plotly("games_rating_by_year.html", platform_traces, {"title":"Backloggd Ratings by Release Year","xaxis":{"title":"Release Year"},"yaxis":{"title":"User Rating"}})

# February games
metas = []
user_by_platform = defaultdict(list)
with open("data/feb_2023/games.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        meta_txt = row.get("metascore", "").strip()
        user_txt = row.get("user_score", "").strip()
        platform = row.get("platform", "").strip() or "Unknown"
        if meta_txt.isdigit():
            metas.append(int(meta_txt))
        try:
            user = float(user_txt)
        except ValueError:
            continue
        user_by_platform[platform].append(user)

if metas:
    bins = [0]*10
    for score in metas:
        idx = min(score // 10, 9)
        bins[idx] += 1
    labels = [f"{i*10}-{i*10+9}" for i in range(10)]
    write_svg_bar("feb_metascore_histogram.svg", "Metascore Distribution", labels, bins, "Games")
platforms = sorted(user_by_platform.items(), key=lambda kv: mean(kv[1]), reverse=True)
bar_trace = [{"type":"bar","name":"User Score","x":[p for p,_ in platforms],"y":[round(mean(vals),2) for _,vals in platforms],"hovertemplate":"%{x}<br>Score: %{y}<extra></extra>"}]
write_plotly("feb_user_score_by_platform.html", bar_trace, {"title":"Average User Score by Platform","xaxis":{"title":"Platform"},"yaxis":{"title":"Average User Score"}})
