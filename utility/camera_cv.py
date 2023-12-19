# Train model to recognize human facial features
import cv2
import numpy as np
import os


class Detector:
    def __init__(self, xml_path, color, label, scaleFactor=1.1, minNeighbors=5):
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + xml_path)
        self.color = color
        self.label = label
        self.scaleFactor = scaleFactor
        self.minNeighbors = minNeighbors

    def detect(self, gray):
        return self.cascade.detectMultiScale(gray, self.scaleFactor, self.minNeighbors)


def draw_rectangle(frame, x, y, w, h, color, label):
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)


def train_recognizer(data_folder):
    images = []
    labels = []
    label_dict = {}
    current_label = 0

    for person_name in os.listdir(data_folder):
        person_folder = os.path.join(data_folder, person_name)
        if os.path.isdir(person_folder):
            for image_name in os.listdir(person_folder):
                image_path = os.path.join(person_folder, image_name)
                image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
                images.append(image)
                labels.append(current_label)
            label_dict[current_label] = person_name
            current_label += 1

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    print(f"Total Images: {len(images)}")
    print(f"Total Labels: {len(labels)}")
    for label, name in label_dict.items():
        print(f"Label: {label}, Name: {name}")
        recognizer.train(images, np.array(labels))
        recognizer.save(f"people_data/trained_model_{name}.yml")
    return recognizer, label_dict


def main():
    cap = cv2.VideoCapture(0)

    detectors = {
        "face": Detector('haarcascade_frontalface_default.xml', (0, 255, 0), "Face"),
        "eye": Detector(xml_path='haarcascade_eye.xml', color=(255, 0, 0), label='eye')
    }

    recognizer, label_dict = train_recognizer("Directory")

    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.putText(frame, "Training model ", (frame.shape[1] - 400, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                    (0, 0, 255), 1)

        for detector_name, detector in detectors.items():
            detections = detector.detect(gray)
            for (x, y, w, h) in detections:
                if detector_name == "face":
                    roi_gray = gray[y:y + h, x:x + w]
                    label, confidence = recognizer.predict(roi_gray)
                    person_name = label_dict.get(label, "Unknown")
                    cv2.putText(frame, f"{person_name} - {confidence:.2f}%", (x, y - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                                (255, 255, 0), 1)
                draw_rectangle(frame, x, y, w, h, detector.color, detector.label)

        cv2.imshow('Model Training for detection', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

