### file: README.md

```
# RushCheck — Local Run

1. Ensure Python and pip are installed.
2. Place video files under `videos/` and thumbnails under `static/images/` matching keys in `LOCATIONS` in `app.py`.
3. Install dependencies:
   pip install -r requirements.txt
4. Run the server:
   python app.py
5. Visit http://127.0.0.1:5000/

Notes:
- First run of YOLO may download model weights.
- The app stores results in `data.sqlite` in the project root.
```
