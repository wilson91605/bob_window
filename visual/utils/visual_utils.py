from typing import Optional

import cv2


def annotateLabel(image, x, y, width, height, label) -> Optional:
    result = image
    cv2.rectangle(result, (x, y), (x + width, y + height),
                  (0, 255, 0), 2)
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(result, label,
                (x, y - 10), font,
                1, (0, 0, 255), 2, cv2.LINE_4)

    return result
