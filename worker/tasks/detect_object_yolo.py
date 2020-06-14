
import asyncio
import os
import cv2


async def detect(conf, frame, pyo, net, ln, LABELS, COLORS):

    H, W = frame.shape[:2]

    print("[INFO] Creating blob from frame")
    # construct a blob from the input frame and then perform
    # a forward pass of the YOLO object detector, giving us
    # our bounding boxes and associated probabilities
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0,
                                 (416, 416), swapRB=True, crop=False)

    await asyncio.sleep(0.1)

    print("[INFO] Forward pass on network")
    net.setInput(blob)
    layerOutputs = net.forward(ln)
    await asyncio.sleep(0.1)

    print("[INFO] Parse YOLO v4 output")
    (boxes, confidences, classIDs) = pyo.parse(layerOutputs,
                                               LABELS, H, W)
    await asyncio.sleep(0.1)

    print("[INFO] Apply non-maxima")
    # apply non-maxima suppression to suppress weak,
    # overlapping bounding boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences,
                            conf["confidence"], conf["threshold"])

    await asyncio.sleep(0.1)

    print("[INFO] Check if detection exists")
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            detected_class = LABELS[classIDs[i]]

            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the frame
            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(frame, (x, y), (x + w, y + h),
                          color, 2)
            text = "{}: {:.4f}".format(detected_class,
                                       confidences[i])
            y = (y - 15) if (y - 15) > 0 else h - 15
            cv2.putText(frame, text, (x, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return frame

    return None
