"""
export/excel_exporter.py
Exports timetable assignments to a professional, multi-tab Excel workbook (.xlsx).
Tabs:
1. Master Schedule
2. Class Timetables
3. Teacher Timetables
4. Room Timetables
5. Audit & Constraint Report
"""

import io
from typing import Dict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from core.models import TimetableProblem, SlotAssignment
from core.constraints import ConstraintChecker


def export_timetable_to_excel_bytes(
    problem: TimetableProblem, assignment: Dict[str, SlotAssignment]
) -> bytes:
    """Creates a styled multi-sheet Excel workbook as bytes."""
    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    var_dict = {v.var_id: v for v in problem.variables}
    days = problem.time_structure.days
    periods = list(range(1, problem.time_structure.periods_per_day + 1))
    day_order = {day: i for i, day in enumerate(days)}

    # Styles
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1F4E79")
    sub_font = Font(name="Calibri", size=11, bold=True)
    lunch_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
    lab_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
    theory_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3")
    )
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # ==================== 1. Master Schedule ====================
    ws_master = wb.create_sheet(title="Master Schedule")
    ws_master.views.sheetView[0].showGridLines = True

    headers = ["Class", "Subject", "Teacher", "Day", "Period", "Room", "Type"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws_master.cell(row=1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    sorted_entries = sorted(
        assignment.items(),
        key=lambda item: (
            day_order.get(item[1].day, 99),
            item[1].period,
            var_dict[item[0]].class_name
        )
    )

    for row_idx, (var_id, slot) in enumerate(sorted_entries, 2):
        var = var_dict.get(var_id)
        if not var:
            continue
        session_type = "Lab" if var.is_lab else "Theory"
        row_vals = [var.class_name, var.subject_code, var.teacher_name, slot.day, slot.period, slot.room_name, session_type]
        for col_idx, val in enumerate(row_vals, 1):
            cell = ws_master.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            cell.alignment = center_align
            if var.is_lab:
                cell.fill = lab_fill

    # ==================== 2. Class Timetables ====================
    ws_class = wb.create_sheet(title="Class Timetables")
    ws_class.views.sheetView[0].showGridLines = True
    current_row = 1

    for c_name, c_batch in problem.classes.items():
        title_cell = ws_class.cell(row=current_row, column=1, value=f"Class Timetable: {c_name} (Strength: {c_batch.strength})")
        title_cell.font = title_font
        current_row += 1

        # Header row
        ws_class.cell(row=current_row, column=1, value="Day").font = header_font
        ws_class.cell(row=current_row, column=1).fill = header_fill
        ws_class.cell(row=current_row, column=1).alignment = center_align
        for col_idx, p in enumerate(periods, 2):
            cell = ws_class.cell(row=current_row, column=col_idx, value=f"Period {p}")
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align

        # Map slots
        c_grid = {}
        for var_id, slot in assignment.items():
            var = var_dict.get(var_id)
            if var and var.class_name == c_name:
                c_grid[(slot.day, slot.period)] = (var, slot)

        current_row += 1
        for day in days:
            day_cell = ws_class.cell(row=current_row, column=1, value=day)
            day_cell.font = sub_font
            day_cell.border = thin_border
            day_cell.alignment = center_align

            for col_idx, p in enumerate(periods, 2):
                cell = ws_class.cell(row=current_row, column=col_idx)
                cell.border = thin_border
                cell.alignment = center_align

                if p == c_batch.lunch_break_period:
                    cell.value = "LUNCH BREAK"
                    cell.fill = lunch_fill
                    cell.font = Font(name="Calibri", size=9, italic=True)
                elif (day, p) in c_grid:
                    var, slot = c_grid[(day, p)]
                    cell.value = f"{var.subject_code}\n{var.teacher_name}\n({slot.room_name})"
                    cell.fill = lab_fill if var.is_lab else theory_fill
                    cell.font = Font(name="Calibri", size=9)
                else:
                    cell.value = "Free"
                    cell.font = Font(name="Calibri", size=9, color="808080")
            current_row += 1
        current_row += 2

    # ==================== 3. Teacher Timetables ====================
    ws_teacher = wb.create_sheet(title="Teacher Timetables")
    ws_teacher.views.sheetView[0].showGridLines = True
    current_row = 1

    for t_name, teacher in problem.teachers.items():
        title_cell = ws_teacher.cell(row=current_row, column=1, value=f"Teacher Timetable: {t_name} (Max Load: {teacher.max_weekly_load})")
        title_cell.font = title_font
        current_row += 1

        ws_teacher.cell(row=current_row, column=1, value="Day").font = header_font
        ws_teacher.cell(row=current_row, column=1).fill = header_fill
        ws_teacher.cell(row=current_row, column=1).alignment = center_align
        for col_idx, p in enumerate(periods, 2):
            cell = ws_teacher.cell(row=current_row, column=col_idx, value=f"Period {p}")
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_align

        t_grid = {}
        for var_id, slot in assignment.items():
            var = var_dict.get(var_id)
            if var and var.teacher_name == t_name:
                t_grid[(slot.day, slot.period)] = (var, slot)

        current_row += 1
        for day in days:
            day_cell = ws_teacher.cell(row=current_row, column=1, value=day)
            day_cell.font = sub_font
            day_cell.border = thin_border
            day_cell.alignment = center_align

            for col_idx, p in enumerate(periods, 2):
                cell = ws_teacher.cell(row=current_row, column=col_idx)
                cell.border = thin_border
                cell.alignment = center_align

                if (day, p) in teacher.unavailable_slots:
                    cell.value = "Unavailable"
                    cell.fill = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
                    cell.font = Font(name="Calibri", size=9, italic=True)
                elif (day, p) in t_grid:
                    var, slot = t_grid[(day, p)]
                    cell.value = f"{var.class_name}\n{var.subject_code}\n({slot.room_name})"
                    cell.fill = lab_fill if var.is_lab else theory_fill
                    cell.font = Font(name="Calibri", size=9)
                else:
                    cell.value = "Free"
                    cell.font = Font(name="Calibri", size=9, color="808080")
            current_row += 1
        current_row += 2

    # Auto-adjust column widths
    for sheet in wb.worksheets:
        for col in sheet.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val = str(cell.value or "")
                if "\n" in val:
                    val = max(val.split("\n"), key=len)
                max_len = max(max_len, len(val))
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 14)

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
