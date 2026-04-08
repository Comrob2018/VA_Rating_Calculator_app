import sys
import re
import os
from typing import List, Tuple, Dict, Optional

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QTextEdit,
    QHeaderView,
    QFileDialog,
    QCheckBox,
)
from PyQt6.QtCore import Qt


def va_combined_rating_detailed(ratings: List[float]) -> Tuple[int, List[Dict]]:
    """
    Calculate VA combined disability rating and return detailed steps.

    Args:
        ratings: List of individual ratings (e.g. [50, 30, 10])

    Returns:
        final_rating: final combined rating rounded to nearest 10
        steps: list of dicts with per-step breakdown
    """
    if not ratings:
        return 0, []

    clean_ratings = sorted(
        [float(r) for r in ratings if 0 < float(r) <= 100],
        reverse=True,
    )
    if not clean_ratings:
        return 0, []

    combined = 0.0
    steps = []

    for r in clean_ratings:
        remaining = 100.0 - combined
        added = remaining * (r / 100.0)

        before_round_combined = combined + added
        combined = round(before_round_combined)

        steps.append({
            "rating": r,
            "remaining_before": remaining,
            "added": added,
            "combined_before_round": before_round_combined,
            "combined_after_round": None,
        })

    # Clamp between 0 and 100
    combined = before_round_combined

    # Final rounding to nearest 10 (5 rounds up)
    remainder = combined % 10
    if remainder >= 5:
        final = combined + (10 - remainder)
    else:
        final = combined - remainder
    
    if steps:
        steps[-1]["combined_after_round"] = int(final)

    return int(final), steps


def parse_va_pdf(pdf_path: str) -> Tuple[List[Tuple[str, float]], Optional[str]]:
    """
    Parse a VA rating decision PDF and extract conditions with their ratings.

    Args:
        pdf_path: Path to the VA PDF file

    Returns:
        conditions: List of (condition_name, rating) tuples for compensable (>0) ratings
        error: Error message string, or None on success
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return [], "pypdf is not installed. Run: pip install pypdf"

    try:
        r = PdfReader(pdf_path)
    except Exception as e:
        return [], f"Could not open PDF: {e}"

    full_text = ""
    for page in r.pages:
        full_text += page.extract_text() + "\n"

    # Find the DECISION section (present in Rating Decision pages)
    decision_match = re.search(r"\bDECISION\b\s*\n(.+?)(?:EVIDENCE|REASONS FOR DECISION)", full_text, re.DOTALL)
    if not decision_match:
        return [], "Could not find a DECISION section in the PDF. Make sure this is a VA Rating Decision letter."

    decision_text = decision_match.group(1)

    # Split on numbered items like "1. Service connection for ..."
    lines = decision_text.split("\n")
    blocks = []
    current = ""
    for line in lines:
        if re.match(r"^\d+\.\s+Service connection", line.strip()):
            if current:
                blocks.append(current)
            current = line.strip()
        else:
            current += " " + line.strip()
    if current:
        blocks.append(current)

    conditions = []
    seen = set()
    for block in blocks:
        m = re.search(
            r"Service connection for (.+?) is granted with an evaluation of (\d+) percent",
            block,
        )
        if m:
            cond = re.sub(r"\s+", " ", m.group(1)).strip()
            # Strip parenthetical "claimed as ..." suffix
            cond = re.sub(r"\s*\(claimed as .+?\)\s*$", "", cond, flags=re.IGNORECASE).strip()
            # Normalize capitalization
            cond = cond[0].upper() + cond[1:] if cond else cond
            rating = int(m.group(2))
            key = cond.lower()
            if key not in seen:
                seen.add(key)
                conditions.append((cond, float(rating)))

    if not conditions:
        return [], "No service-connected conditions found in the DECISION section."

    return conditions, None


class VaMathApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VA Combined Rating Calculator")
        self.resize(750, 600)
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        # --- PDF import row ---
        pdf_layout = QHBoxLayout()
        load_button = QPushButton("Load Conditions from PDF...")
        load_button.clicked.connect(self._browse_and_load_pdf)
        pdf_layout.addWidget(load_button)
        pdf_layout.addStretch()
        main_layout.addLayout(pdf_layout)

        # --- Checkbox: include 0% conditions ---
        self.include_zero_cb = QCheckBox("Include 0% (non-compensable) conditions when loading PDF")
        self.include_zero_cb.setChecked(False)
        main_layout.addWidget(self.include_zero_cb)

        # --- Input row: condition name + rating + add button ---
        input_layout = QHBoxLayout()

        self.condition_input = QLineEdit()
        self.condition_input.setPlaceholderText("Condition name (e.g., PTSD)")

        self.rating_input = QLineEdit()
        self.rating_input.setPlaceholderText("Rating % (e.g., 50)")

        add_button = QPushButton("Add Condition")
        add_button.clicked.connect(self.add_condition)

        input_layout.addWidget(self.condition_input)
        input_layout.addWidget(self.rating_input)
        input_layout.addWidget(add_button)

        main_layout.addLayout(input_layout)

        # --- Table of conditions ---
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Condition", "Rating (%)"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        main_layout.addWidget(self.table)

        # --- Buttons under table ---
        button_row = QHBoxLayout()

        remove_button = QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_selected)

        clear_button = QPushButton("Clear All")
        clear_button.clicked.connect(self.clear_all)

        calc_button = QPushButton("Calculate Combined Rating")
        calc_button.clicked.connect(self.calculate_rating)

        button_row.addWidget(remove_button)
        button_row.addWidget(clear_button)
        button_row.addStretch()
        button_row.addWidget(calc_button)

        main_layout.addLayout(button_row)

        # --- Result display ---
        result_row = QHBoxLayout()
        self.result_label = QLabel("Combined Rating: -- %")
        self.result_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.actual_label = QLabel("Actual: -- %")
        self.actual_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        self.remaining_label = QLabel("Remaining to 100%: -- %")
        self.remaining_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #555;")
        result_row.addWidget(self.result_label)
        result_row.addSpacing(20)
        result_row.addWidget(self.actual_label)
        result_row.addSpacing(20)
        result_row.addWidget(self.remaining_label)
        result_row.addStretch()
        main_layout.addLayout(result_row)

        self.details_box = QTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.setPlaceholderText("Calculation steps will appear here...")
        main_layout.addWidget(self.details_box)

    # ----------------------------
    #      PDF Loading
    # ----------------------------

    def _browse_and_load_pdf(self):
        pdf_path, _ = QFileDialog.getOpenFileName(
            self, "Select VA Rating Decision PDF", "", "PDF Files (*.pdf);;All Files (*)"
        )
        if not pdf_path:
            return

        conditions, error = parse_va_pdf(pdf_path)
        if error:
            QMessageBox.critical(self, "PDF Parse Error", error)
            return

        include_zero = self.include_zero_cb.isChecked()
        filtered = [(c, r) for c, r in conditions if include_zero or r > 0]

        if not filtered:
            msg = "No compensable (>0%) conditions found in the PDF."
            if not include_zero:
                msg += "\n\nTip: Check 'Include 0% conditions' if you want to load all service-connected conditions."
            QMessageBox.information(self, "No Conditions Found", msg)
            return

        # Clear existing rows and populate from PDF
        self.table.setRowCount(0)
        self.result_label.setText("Combined Rating: -- %")
        self.details_box.clear()

        for condition, rating in filtered:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(condition))
            self.table.setItem(row, 1, QTableWidgetItem(str(int(rating))))

        total = len(filtered)
        zero_count = sum(1 for _, r in filtered if r == 0)
        msg = f"Loaded {total} condition(s) from PDF."
        if zero_count and include_zero:
            msg += f"\n({zero_count} with 0% rating - these won't affect the combined score.)"
        QMessageBox.information(self, "PDF Loaded", msg)

    # ----------------------------
    #      Actions / Handlers
    # ----------------------------

    def add_condition(self):
        name = self.condition_input.text().strip()
        rating_text = self.rating_input.text().strip()

        if not rating_text:
            QMessageBox.warning(self, "Input Error", "Please enter a rating percentage.")
            return

        try:
            rating = float(rating_text)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Rating must be a number.")
            return

        if rating < 0 or rating > 100:
            QMessageBox.warning(self, "Input Error", "Rating must be between 0 and 100.")
            return

        if not name:
            name = f"Condition {self.table.rowCount() + 1}"

        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(str(rating)))

        # Clear inputs
        self.condition_input.clear()
        self.rating_input.clear()
        self.condition_input.setFocus()

    def remove_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "Remove Selected", "No row selected.")
            return

        for row in rows:
            self.table.removeRow(row)

    def clear_all(self):
        self.table.setRowCount(0)
        self.result_label.setText("Combined Rating: -- %")
        self.actual_label.setText("Actual: -- %")
        self.remaining_label.setText("Remaining to 100%: -- %")
        self.details_box.clear()

    def calculate_rating(self):
        ratings = []
        conditions = []

        for row in range(self.table.rowCount()):
            condition_item = self.table.item(row, 0)
            rating_item = self.table.item(row, 1)

            if rating_item is None:
                continue

            condition_name = condition_item.text() if condition_item else f"Condition {row + 1}"
            rating_text = rating_item.text().strip()

            try:
                rating = float(rating_text)
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Data Error",
                    f"Invalid rating in row {row + 1}: '{rating_text}'",
                )
                return

            if rating < 0 or rating > 100:
                QMessageBox.warning(
                    self,
                    "Data Error",
                    f"Rating in row {row + 1} must be between 0 and 100.",
                )
                return

            conditions.append((condition_name, rating))
            ratings.append(rating)

        if not ratings:
            QMessageBox.information(self, "No Data", "Please add at least one condition.")
            return

        final_rating, steps = va_combined_rating_detailed(ratings)

        # Compute actual (unrounded) combined value from the last step
        actual = steps[-1]["combined_before_round"] if steps else 0.0
        remaining = 95.0 - actual

        # Update result labels
        self.result_label.setText(f"Combined Rating: {final_rating}%")
        self.actual_label.setText(f"Actual: {actual:.2f}%")
        self.remaining_label.setText(f"Remaining to 95%: {remaining:.2f}%")

        # Build a nice readable step-by-step breakdown
        details_lines = []

        # Show sorted conditions with ratings
        details_lines.append("Conditions (sorted by rating):")
        for name, r in sorted(conditions, key=lambda x: x[1], reverse=True):
            details_lines.append(f"  - {name}: {r:.0f}%")
        details_lines.append("")

        # Build a lookup from rating order (steps are sorted by rating descending)
        sorted_conditions = sorted(conditions, key=lambda x: x[1], reverse=True)

        details_lines.append("Calculation Steps (0% conditions are excluded from math):")
        for idx, step in enumerate(steps, start=1):
            cond_name = sorted_conditions[idx - 1][0] if idx - 1 < len(sorted_conditions) else "Unknown"
            details_lines.append(f"Step {idx}: {step['rating']:.0f}% - {cond_name}")
            details_lines.append(f"  Remaining before: {step['remaining_before']:.2f}%")
            details_lines.append(f"  Added: {step['added']:.2f}%")
            details_lines.append(f"  Actual percentage: {step['combined_before_round']:.2f}%")
            details_lines.append("")

        details_lines.append(f"Final VA combined rating (rounded to nearest 10): {final_rating}%")

        self.details_box.setPlainText("\n".join(details_lines))


def main():
    app = QApplication(sys.argv)
    window = VaMathApp()

    # Auto-load PDF if passed as command-line argument
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        conditions, error = parse_va_pdf(sys.argv[1])
        if not error:
            for condition, rating in conditions:
                if rating > 0:
                    row = window.table.rowCount()
                    window.table.insertRow(row)
                    window.table.setItem(row, 0, QTableWidgetItem(condition))
                    window.table.setItem(row, 1, QTableWidgetItem(str(int(rating))))

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
