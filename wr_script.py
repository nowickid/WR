#!/usr/bin/env python3
from ev3dev2.motor import MoveTank, OUTPUT_A, OUTPUT_B, OUTPUT_C, Motor
from ev3dev2.sensor.lego import ColorSensor, TouchSensor
from ev3dev2.sensor import INPUT_1, INPUT_2, INPUT_3
import time

BASE_SPEED = 0
MAX_BASE_SPEED = -15
SPEED_INCREMENT = 1
CORRECTION_MULTIPLIER = 30
CORRECTION_MAX = 70
MAX_REVERSING = 25

m1 = Motor(OUTPUT_A)
m2 = Motor(OUTPUT_B)
m3 = Motor(OUTPUT_C)
tank = MoveTank(OUTPUT_A, OUTPUT_B)
button = TouchSensor(INPUT_3)
left_sensor = ColorSensor(INPUT_1)
right_sensor = ColorSensor(INPUT_2)


class Color(Enum):
    WHITE = 0
    BLACK = 1
    RED = 2
    BLUE = 3


def determine_turn_direction():
    l_color = left_sensor.color
    r_color = right_sensor.color

    if l_color == r_color:
        return 0
    elif l_color == Color.BLACK:
        return -1
    elif r_color == Color.BLACK:
        return 1
    return 0


def calc_correction(current_correction, current_drive, direction, last_direction):
    rotate = 0
    drive = 0
    if direction == 0:
        if direction == last_direction:
            drive = current_drive - SPEED_INCREMENT
    elif direction == last_direction:
        if current_correction > 0:
            rotate = current_correction + 1
        else:
            rotate = current_correction - 1
    else:
        rotate = direction

    return (max(drive, MAX_BASE_SPEED), rotate)


def calc_correction_percentage(correction):
    correction_percentage = correction * CORRECTION_MULTIPLIER
    if correction_percentage > CORRECTION_MAX:
        return CORRECTION_MAX
    elif correction_percentage < -CORRECTION_MAX:
        return -CORRECTION_MAX
    return correction_percentage


def follow_line(correction, last_direction, drive):
    direction = determine_turn_direction()
    drive, correction = calc_correction(correction, drive, direction, last_direction)
    last_direction = direction
    correction_percentage = calc_correction_percentage(correction)
    tank.on(min(BASE_SPEED + drive - correction_percentage, MAX_REVERSING),
            min(BASE_SPEED + drive + correction_percentage, MAX_REVERSING))
    return last_direction, correction, drive


def pick_box():
    for i in range(1):
        tank.on_for_degrees(100, 100, -220)
    time.sleep(1)
    m3.on_for_degrees(100, 2250)  # podnoszenie
    time.sleep(1)
    m1.on_for_degrees(100, 530)
    m2.on_for_degrees(100, -530)


def place_box():
    tank.on_for_degrees(100, 100, 300)
    m3.on_for_degrees(100, -2250)  # opuszczanie
    time.sleep(1)
    for i in range(1):
        tank.on_for_degrees(100, 100, 220)
    time.sleep(1)
    time.sleep(1)
    m1.on_for_degrees(100, 530)
    m2.on_for_degrees(100, -530)


def turn(dir):
    if dir == "R":
        tank.on_for_degrees(100, 100, -110)
        m1.on_for_degrees(100, -500)
    elif dir == "L":
        tank.on_for_degrees(100, 100, -110)
        m2.on_for_degrees(100, -500)


def convert_color(color):
    if color == 5:
        return Color.RED
    if color == 1:
        return Color.BLACK
    return 0


TRANSPORTER_ACTIVE = True

state = 0
correction = 0
last_direction = 0
drive = 0
while (1):
    if (not TRANSPORTER_ACTIVE):
        last_direction, correction, drive = follow_line(correction, last_direction, drive)

    else:
        colorL = convert_color(left_sensor.color)
        colorR = convert_color(right_sensor.color)

        if state == 0:
            MAX_BASE_SPEED = -75
            SPEED_INCREMENT = 20
            CORRECTION_MULTIPLIER = 40
            CORRECTION_MAX = 80
            MAX_REVERSING = 30
            tank.on(0, 0)
            if button.is_pressed:
                state = 1

        elif state == 1:
            last_direction, correction, drive = follow_line(correction, last_direction, drive)
            if (colorL == Color.RED):
                turn("L")
                state = 2
            elif (colorR == Color.RED):
                turn("R")
                state = 2
        elif state == 2:
            last_direction, correction, drive = follow_line(correction, last_direction, drive)
            if ((colorL == Color.RED) and (colorR == Color.RED)):
                pick_box()
                state = 3
                MAX_BASE_SPEED = -20
        elif state == 3:
            last_direction, correction, drive = follow_line(correction, last_direction, drive)
            if ((colorL == Color.BLACK) and (colorR == Color.BLACK)):
                turn("L")
                state = 4
        elif state == 4:
            last_direction, correction, drive = follow_line(correction, last_direction, drive)
            if (colorR == Color.RED):
                turn("R")
                state = 5
                MAX_BASE_SPEED = -75
        elif state == 5:
            last_direction, correction, drive = follow_line(correction, last_direction, drive)
            if ((colorL == Color.RED) and (colorR == Color.RED)):
                place_box()
                state = 0
