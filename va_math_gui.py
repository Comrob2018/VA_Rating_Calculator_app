import sys
from typing import List, Tuple, Dict

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
)


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
            "combined_after_round": combined,
        })

    # Clamp between 0 and 100
    combined = min(100, max(0, int(round(combined))))

    # Final rounding to nearest 10 (5 rounds up)
    remainder = combined % 10
    if remainder >= 5:
        final = combined + (10 - remainder)
    else:
        final = combined - remainder

    return int(final), steps


class VaMathApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VA Combined Rating Calculator")
        self.resize(700, 500)

        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

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
        self.result_label = QLabel("Combined Rating: -- %")
        self.result_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(self.result_label)

        self.details_box = QTextEdit()
        self.details_box.setReadOnly(True)
        self.details_box.setPlaceholderText("Calculation steps will appear here...")
        main_layout.addWidget(self.details_box)

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

        if rating <= 0 or rating > 100:
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

            if rating <= 0 or rating > 100:
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

        # Update main result label
        self.result_label.setText(f"Combined Rating: {final_rating} %")

        # Build a nice readable step-by-step breakdown
        details_lines = []

        # Show sorted conditions with ratings
        details_lines.append("Conditions (sorted by rating):")
        for name, r in sorted(conditions, key=lambda x: x[1], reverse=True):
            details_lines.append(f"  - {name}: {r:.0f}%")
        details_lines.append("")

        details_lines.append("Calculation Steps:")
        for idx, step in enumerate(steps, start=1):
            details_lines.append(f"Step {idx}: {step['rating']:.0f}% condition")
            details_lines.append(f"  Remaining before: {step['remaining_before']:.2f}%")
            details_lines.append(f"  Added: {step['added']:.2f}%")
            details_lines.append(f"  Combined before round: {step['combined_before_round']:.2f}%")
            details_lines.append(f"  Combined after round: {step['combined_after_round']}%")
            details_lines.append("")

        details_lines.append(f"Final VA combined rating (rounded to nearest 10): {final_rating}%")

        self.details_box.setPlainText("\n".join(details_lines))


def main():
    app = QApplication(sys.argv)
    window = VaMathApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()