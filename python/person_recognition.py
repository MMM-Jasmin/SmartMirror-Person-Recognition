import math
import random
import cv2
import json, sys
import numpy as np
import time, threading

def to_node(type, message):
        # convert to json and print (node helper will read from stdout)
        try:
                print(json.dumps({type: message}))
        except Exception:
                pass
        # stdout has to be flushed manually to prevent delays in the node helper communication
        sys.stdout.flush()

maxIOFaceToPersonRating = 0.7
confidenceTreshhold = 0.7
# Result dict
person_dict = {}
last_person_dict = {}


#Full HD image as default
IMAGE_HEIGHT = 1080
IMAGE_WIDTH = 1920

try:
        to_node("status", "starting with config: " + sys.argv[1])
        config = json.loads(sys.argv[1])
        if 'image_height' in config:
                IMAGE_HEIGHT = int(config['image_height'])
        if 'image_width' in config:
                IMAGE_WIDTH = int(config['image_width'])
except:
        to_node("status", "starting without config as it was not readable/existent")


def convertBack(x, y, w, h):
        x = x * IMAGE_WIDTH
        y = y * IMAGE_HEIGHT
        w = w * IMAGE_WIDTH
        h = h * IMAGE_HEIGHT
        xmin = int(round(x - (w / 2)))
        xmax = int(round(x + (w / 2)))
        ymin = int(round(y - (h / 2)))
        ymax = int(round(y + (h / 2)))
        return ((xmin, ymin),(xmax, ymax))

def to_node(type, message):
        # convert to json and print (node helper will read from stdout)
        try:
                print(json.dumps({type: message}))
        except Exception:
                pass
        # stdout has to be flushed manually to prevent delays in the node helper communication
        sys.stdout.flush()


# data structure
# {"DETECTED_OBJECTS": [{"TrackID": 1.0, "center": [0.12593, 0.7125], "name": "chair", "w_h": [0.2463, 0.15417]}, {"TrackID": 3.0, "center": [0.18889, 0.79167], "name": "bottle", "w_h": [0.10741, 0.1724]}]}

def contains(r1, r2):
        # return r1.x1 < r2.x1 < r2.x2 < r1.x2 and r1.y1 < r2.y1 < r2.y2 < r1.y2
        return r1[0][0] < r2[0][0] < r2[1][0] < r1[1][0] and r1[0][1] < r2[0][1] < r2[1][1] < r1[1][1]

def get_intersection_ratio(bb_a,bb_b):
        """
        Computes ratio of area of bbox b in a of boxform [[x1,y1],[x2,y2]]
        """
        xx1 = np.maximum(bb_a[0][0], bb_b[0][0])
        yy1 = np.maximum(bb_a[0][1], bb_b[0][1])
        xx2 = np.minimum(bb_a[1][0], bb_b[1][0])
        yy2 = np.minimum(bb_a[1][1], bb_b[1][1])
        w = np.maximum(0., xx2 - xx1)
        h = np.maximum(0., yy2 - yy1)
        wh = w * h
        o = wh / ((bb_b[1][0]-bb_b[0][0])*(bb_b[1][1]-bb_b[0][1]))
        #o = wh / ((bb_test[1][0]-bb_test[0][0])*(bb_test[1][1]-bb_test[0][1]) + (bb_gt[1][0]-bb_gt[0][0])*(bb_gt[1][1]-bb_gt[0][1]) - wh)
        return(o)

def bb_intersection_over_union(boxA, boxB):
        # determine the (x, y)-coordinates of the intersection rectangle
        xA = max(boxA[0][0], boxB[0][0])
        yA = max(boxA[0][1], boxB[0][1])
        xB = min(boxA[1][0], boxB[1][0])
        yB = min(boxA[1][1], boxB[1][1])

        # compute the area of intersection rectangle
        interArea = abs(max((xB - xA, 0)) * max((yB - yA), 0))
        if interArea == 0:
                return 0
        # compute the area of both the prediction and ground-truth
        # rectangles
        boxAArea = abs((boxA[1][0] - boxA[0][0]) * (boxA[1][1] - boxA[0][1]))
        boxBArea = abs((boxB[1][0] - boxB[0][0]) * (boxB[1][1] - boxB[0][1]))

        # compute the intersection over union by taking the intersection
        # area and dividing it by the sum of prediction + ground-truth
        # areas - the interesection area
        iou = interArea / float(boxAArea + boxBArea - interArea)

        # return the intersection over union value
        return iou

def check_stdin():
        global person_dict
        while True:
                try:
                        lines = sys.stdin.readline()
                        data = json.loads(lines)
                        if 'DETECTED_FACES' in data:
                                dict_faces = data['DETECTED_FACES']
                                #to_node("status", data['DETECTED_FACES'])
                                for face in dict_faces:

                                        rect_face = convertBack(face["center"][0], face["center"][1], face["w_h"][0], face["w_h"][1] )

                                        for person in person_dict.keys():
                                                rect_person = convertBack(person_dict[person]["center"][0], person_dict[person]["center"][1], person_dict[person]["w_h"][0], person_dict[person]["w_h"][1])

                                                if contains(rect_person, rect_face) and (bb_intersection_over_union(rect_person, rect_face) < maxIOFaceToPersonRating):
                                                        #to_node("status", "Found object person (ID " + str(person_dict[person]["TrackID"]) + ") that contains a face (ID " + str(face["TrackID"]))
                                                        if "face" in person_dict[person]:
                                                                if face["ID"] is person_dict[person]["face"]["ID"]:
                                                                        person_dict[person]["face"] = face.copy()
                                                                elif face["confidence"] > confidenceTreshhold and person_dict[person]["face"]["confidence"] < confidenceTreshhold:
                                                                        person_dict[person]["face"] = face.copy()
                                                                elif face["confidence"] > (person_dict[person]["face"]["confidence"] + 0.1):
                                                                        person_dict[person]["face"] = face.copy()
                                                                else:
                                                                        person_dict[person]["face"]["confidence"] -= 0.001
                                                        else:
                                                                person_dict[person]["face"] = face.copy()

                                for person in person_dict.keys():
                                        if "face" in person_dict[person]:
                                                if not "center" in person_dict[person]["face"]:
                                                        continue
                                                found = False
                                                for face in dict_faces:
                                                        if (sorted(person_dict[person]["face"].items()) == sorted(face.items())):
                                                                found = True
                                                if found is False:
                                                        person_dict[person]["face"].pop("center")


                        elif 'DETECTED_GESTURES' in data:
                                dict_gestures = data['DETECTED_GESTURES']
                                #to_node("status", data['DETECTED_GESTURES'])

                                for person in person_dict.keys():
                                        if "gestures" in person_dict[person]:
                                                person_dict[person].pop("gestures")

                                        rect_person = convertBack(person_dict[person]["center"][0], person_dict[person]["center"][1], person_dict[person]["w_h"][0], person_dict[person]["w_h"][1])

                                        for gesture in dict_gestures:

                                                rect_gesture = convertBack(gesture["center"][0], gesture["center"][1], gesture["w_h"][0], gesture["w_h"][1])

                                                ir = get_intersection_ratio(rect_person,rect_gesture)

                                                if ir > 0.5:
                                                        if "gestures" in person_dict[person]:
                                                                person_dict[person]["gestures"].append(gesture)
                                                        else:
                                                                person_dict[person]["gestures"] = [gesture]


                        elif 'DETECTED_OBJECTS' in data:
                                dict_objects = data['DETECTED_OBJECTS']
                                #to_node("status", data['DETECTED_OBJECTS'])

                                new_PersonDict = {}
                                for element in dict_objects:
                                        if element["name"] == "person":
                                                if not element["TrackID"] in person_dict:
                                                        new_PersonDict[element["TrackID"]] = element.copy()

                                                        to_node("status", "new person was found")
                                                else:
                                                        new_PersonDict[element["TrackID"]] = person_dict[element["TrackID"]]
                                                        if not new_PersonDict[element["TrackID"]]["center"] == element["center"]:
                                                                new_PersonDict[element["TrackID"]]["center"] = element["center"]
                                                        if not new_PersonDict[element["TrackID"]]["w_h"] == element["w_h"]:
                                                                new_PersonDict[element["TrackID"]]["w_h"] = element["w_h"]



                        person_dict = new_PersonDict

                except:
                        #print("whoopsie!")
                        pass



to_node("status","Entering main loop")

t = threading.Thread(target=check_stdin)
t.start()


while True:
        this_dump = json.dumps(person_dict)
        last_person_dict
        if last_person_dict != this_dump:
                to_node("RECOGNIZED_PERSONS", person_dict)
                last_person_dict = this_dump
        time.sleep(1/30)



