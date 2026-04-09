📘 VA Combined Rating Calculator (GUI App)

A simple, clean, and accurate VA Disability Combined Rating Calculator built in Python + PyQt6.
This tool allows veterans to easily input individual condition ratings and compute their official VA combined disability rating, following actual VA math rules.

Includes:

✔️ Easy-to-use GUI
✔️ Step-by-step calculation breakdown
✔️ Automatic VA rounding rules
✔️ Add, remove, and clear conditions
✔️ Packagable as a Windows .exe
✔️ Custom VA% icon included

🖥️ Features  
⭐ VA Math Engine  
The calculator follows official VA math rules:  
Ratings sorted high → low  
Weighted addition based on remaining efficiency  
Rounding at every step  
Final rounding to nearest 10% (5 rounds up)  

⭐ GUI Application  
Add condition names and ratings  
Remove selected conditions  
Clear all inputs  
See a full breakdown of each VA math step  
Final combined rating shown clearly at the top  

⭐ Standalone EXE  
You can package the program as a portable Windows executable using PyInstaller:  
pyinstaller --onefile --windowed --icon=va_icon.ico va_math_gui.py  

📦 Installation  
1. Clone the Repository  
git clone https://github.com/YourUsername/va-combined-rating-calculator.git  
cd va-combined-rating-calculator  

2. Install Dependencies  
It’s recommended to use a virtual environment.  
pip install -r requirements.txt  

requirements.txt example:  
PyQt6

(PyInstaller is optional unless you want to build an .exe.)  

▶️ Running the Program  
python va_math_gui.py  
  
The GUI will launch, allowing you to load your conditions from your pdf decision letter and break down your rating into steps.  
Once you have all your ratings loaded, you can add new ones or change percentages to see how you get that percentage up to 100%.  

Before selecting a PDF decision letter:  

<img width="739" height="621" alt="image" src="https://github.com/user-attachments/assets/f2595f16-3e8c-4200-8363-1984838e6b81" />  

Ratings loaded into table:  

<img width="729" height="228" alt="Screenshot 2026-04-08 214147" src="https://github.com/user-attachments/assets/2ecfa7cf-c6e9-45e2-a3b4-0eb6d71677fd" />  

Ratings breakdown section:  

<img width="732" height="249" alt="Screenshot 2026-04-08 214204" src="https://github.com/user-attachments/assets/ffcb9782-b427-46d1-b36d-3f7c33d10c42" />  


Rating Calculation Steps:  

<img width="326" height="298" alt="image" src="https://github.com/user-attachments/assets/15f49347-0199-46d8-be80-b367084b55fd" />  


🧮 How VA Math Is Calculated  
Conditions are sorted from highest to lowest.  
Each rating is applied to the remaining efficiency (starting at 100%).  
After each step, total is rounded.  
Final result is rounded to the nearest 10.  

Example:  
Ratings = 50%, 30%, 10%  
Final Combined = 70%  

The app shows this breakdown in detail.  
🛠️ Building a Windows EXE (Optional)  
Install PyInstaller:  
pip install pyinstaller  
Build the executable:  
pyinstaller --onefile --windowed --icon=va_icon.ico va_math_gui.py  


The compiled app will appear in:  
dist/va_math_gui.exe  

You can now distribute this .exe to anyone—no Python required.  

🖼️ Custom App Icon  
The repository includes a VA-style logo (VA%) for use as the app icon.  

Use it with PyInstaller:  

--icon=va_icon.ico  


If you need additional icon styles or resolutions, let me know—I can generate more.  

📁 Project Structure  
├── va_math_gui.py  
├── va_icon.ico  
├── README.md  
└── requirements.txt  

🤝 Contributing  
PRs are welcome—particularly if you want to add:  
Multi-condition grouping  
Export to PDF/CSV  
macOS/Linux builds  
Settings / preferences  

📄 License  
MIT License — free to use, modify, and distribute.  

🪖 Made for Veterans  

I built this tool to help veterans quickly understand their potential combined rating without navigating complex math tables. If you want to add more VA-related automation tools, just let me know—I’ll help build them.
