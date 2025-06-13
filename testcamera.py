#!/usr/bin/env python3
import cv2

def gstreamer_pipeline(
    capture_width=640,
    capture_height=480,
    display_width=640,
    display_height=480,
    framerate=30,
    flip_method=0
):
    return (
        f"v4l2src device=/dev/video0 ! "
        f"video/x-raw, width={capture_width}, height={capture_height}, framerate={framerate}/1 ! "
        f"videoconvert ! "
        f"videoscale ! "
        f"video/x-raw, width={display_width}, height={display_height} ! "
        f"appsink"
    )

def main():
    cap = cv2.VideoCapture(gstreamer_pipeline(), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("❌ Could not open USB camera")
        return

    print("✅ Webcam Test Running. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("⚠️ Frame capture failed")
            break

        cv2.imshow("Webcam Test", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
