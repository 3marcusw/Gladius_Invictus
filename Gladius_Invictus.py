#! /usr/bin/env python
# -*- coding: utf-8 -*-
# Gladius Invictus
# 3d printed 1 pound combat robot
# copyright 2019 3marcusw
# dual licenced under the GPLv3 and the Creative Commons CC BY-SA v4

import os
import sys
from solid import *
from solid.utils import *
from functools import reduce

# What do these letters mean?
# l is always length, h is always height, w is always width, r is always radius
# t is thickness
SEGMENTS = 20


def mirror_copy(vector, obj: OpenSCADObject):
    return obj + mirror(vector)(obj)


def trans(vector, obj: OpenSCADObject):
    return translate(vector)(obj)


def rot(vector, obj: OpenSCADObject):
    return rotate(vector)(obj)


def rounded_triangle(r, l):
    h = l * sqrt(3) / 2
    big_r = l * sqrt(3) / 3
    return left(big_r / 2)(hull()(
        circle(r),
        translate([h, l / 2])(circle(r)),
        translate([h, -l / 2])(circle(r))))


'''make_triangles
    takes r, radius of rounded corner,
    l, length of triangle side (not counting r)
    spacing, the distance between triangle points
    num_x, the number of triangles in x direction
    numy, number of triangles in y direction'''


def make_triangles(r, l, num_x, num_y):
    tri = rounded_triangle(r, l)
    big_r = l * sqrt(3) / 3
    triangles = list()
    for i in range(num_y):
        for j in range(num_x):
            if (j + i) % 2 == 0:
                triangles.append(translate([l * j + 2 * j * r + big_r * j + 1, l * i + i * r])(tri))
            else:
                triangles.append(translate([l * j + 2 * j * r + big_r * j, l * i + i * r])(mirror([1, 0, 0])(tri)))

    return union()(triangles)


def test_truss():
    truss_l = 160
    truss_h = 80
    return square([truss_h, truss_l]) - translate([13, 12, 0])(
        make_triangles2(r=2, l1=6, l2=12, num_x=6, num_y=12))


'''def make_triangles(r, l, num_x, num_y):

    tri = rounded_triangle(r,l)
    big_r = l * sqrt(3) / 3
    triangles = list()
    for i in range(num_y):
        for j in range(num_x):
            if (j+i) % 2 == 0:
                triangles.append(translate([l*j + 2*j*r + big_r*j, l*i + i*r])(tri))
            else:
                triangles.append(translate([l*j + 2*j*r + big_r*j, l*i + i*r])(mirror([1,0,0])(tri)))

    return union()(triangles)
'''


def sweep_about_y(shape: OpenSCADObject, end_angle=180, step_angle=15):
    angles = range(0, end_angle, step_angle)
    shapes = [rotate([0, a, 0])(shape) for a in angles]
    return union()(shapes)





class DriveEsc:
    obj = rot([90, 0, 0], import_("tinyESC_v2.stl"))


class Transmitter:
    h = 3
    w = 18
    l = 26
    obj = cube([l, w, h])

class Wheel:
    w = 12.7 # 0.5inch
    d = 38.1 # 1.5 inch
    r = d / 2
    obj = cylinder(r=r, h=w, center=True)


class DriveSystem:
    exposed_shaft_l = 8.67
    gearbox_l = 9
    motor_l = 17
    total_l = exposed_shaft_l + gearbox_l + motor_l
    h = 10
    w = 12
    collar_h = 0.6
    collar_r = 1.75
    motor_r = 6
    shaft_r = 1.5
    shaft_flat = 1.25
    mount_l = gearbox_l + motor_l + 2
    motor = up(motor_l/2)(cube([h, w, motor_l], center=True)) * cylinder(r=motor_r, h=motor_l)
    gearbox = cube([h, w, gearbox_l], center=True)
    collar = cylinder(r=collar_r, h=collar_h, center=True)
    shaft = cylinder(r=shaft_r, h=exposed_shaft_l, center=True)
    gear_motor = motor + up(motor_l+gearbox_l/2)(gearbox + up(gearbox_l/2+collar_h/2)(
        collar + up(collar_h/2+exposed_shaft_l/2)(shaft)))
    wheel_disp = Wheel.w / 2 + total_l - exposed_shaft_l + collar_h + 1
    clip = mirror_copy([1, 0, 0], trans([-h/2, 0, motor_l+gearbox_l], rot([90, 0, 0], cylinder(
        r=collar_h, h=h / 2, center=True))))
    obj = gear_motor + up(wheel_disp)(Wheel.obj)
    mount = (
        clip + up(mount_l/2 - 2)(
        difference()(
            cube([h+1, w+1, mount_l], center=True),
            up(2)(cube([h-1, w-1, mount_l], center=True)),
            cube([h-3, w-2, mount_l+0.01], center=True))) - gear_motor)

class WeaponMotor:
    r = 17.5
    base_r = 16
    shaft_r = 2.5
    base_l = 9.5  # 47.5 - (18 + 3.5 + 16.5)
    middle_l = 18
    collar_l = 3.5
    exposed_shaft_l = 16.5
    shaft_l = 47.5
    screw_disp1 = sqrt(((25/2)**2)/2)
    screw_disp2 = sqrt(((19/2)**2)/2)
    screw = rot([-90, 0, 0], screw(screw_type='m3', screw_length=8))
    screws = union()(
        trans([-screw_disp1, middle_l - base_l / 2, screw_disp1], screw), # top right
        trans([screw_disp1, middle_l - base_l / 2, -screw_disp1], screw), # bottom left
        trans([-screw_disp2, middle_l - base_l / 2, -screw_disp2], screw), # bottom right
        trans([screw_disp2, middle_l - base_l / 2, screw_disp2], screw) # top left
    )
    bearing = trans([0, -(exposed_shaft_l+0.5), 0], rot([90,0,0], bearing(bearing_type='625')))
    obj = forward(middle_l)(translate([12.45, 13.89, -26.76])(rotate([0, 0, 180])(
        import_("Modified.stl")))) + screws + bearing



class WeaponBlade:
    t = 8.08
    w = 3 * t
    l = 12 * t
    r = sqrt((l/2)**2 + (w/2)**2)
    obj = translate([-w / 2, -t / 2, -l / 2])(cube([w, t, l])) +\
          hull()(
        rotate([90, 0, 0])(cylinder(WeaponMotor.r + 6, t, center=True)),
        translate([-w / 2, -t / 2, -l / 4])(cube([w, t, l / 2]))) \
          - rotate([90, 0, 0])(cylinder(WeaponMotor.r, t, center=True))
    circle = sweep_about_y(obj)


class Frame:

    h, l, w = 90, 120, 135
    theta = 90 - math.degrees(math.atan2(l, h / 2))
    t = 3  # approximate wall thickness
    r = 3  # internal frame fillet radius
    overhang = l / 5
    # spheres on corners of tetrahedron
    s1 = translate([0, 0, h / 2])(sphere(r))
    s2 = translate([0, 0, -h / 2])(sphere(r))
    s3 = translate([l, w / 2, 0])(sphere(r))
    s4 = translate([l, -w / 2, 0])(sphere(r))
    tetrahedron = hull()(s1 + s2 + s3 + s4)
    # spheres on corners of tetrahedron shaped void
    s1i = translate([t + r, 0, h / 2 - t - r])(sphere(r))
    s2i = translate([t + r, 0, -h / 2 + t + r])(sphere(r))
    s3i = translate([l - t - r, w / 2 - t - r, 0])(sphere(r))
    s4i = translate([l - t - r, -w / 2 + t + r, 0])(sphere(r))
    tetrahedron_hole = hull()(s1i + s2i + s3i + s4i)

    spinner_zone = translate([-l / 5, 0, 0])(rotate([90, 0, 0])(
        cylinder(r=WeaponBlade.r + 4, h=WeaponBlade.t + 6, center=True)
    ))
    lid_cylinder = (rot([0, theta, 0], cylinder(r1=1.5*r, r2=0.75*r, h=r*1, center=True)))
    lid_ellipsoid = rot([0, theta, 0], scale([1.25, 1.25, 1])(sphere(r*0.26)))

    # lid_plane_equation: z = -hx/2l + h/2
    # co-ordinates for the sphere in the front corner of the lid
    s1_lid_x = 0.29 * l
    s1_lid_z = -h*s1_lid_x/(2*l) + h/2
    # sphere in the front corner
    s1_lid = trans([s1_lid_x, 0, s1_lid_z], lid_ellipsoid)
    s3_lid_x = 0.83 * l
    s3_lid_z = -h*s3_lid_x/(2*l) + h/2
    s3_lid = trans([s3_lid_x, w/4, s3_lid_z], lid_ellipsoid)
    s4_lid_x = 0.83 * l
    s4_lid_z = -h * s4_lid_x / (2 * l) + h/2
    s4_lid = trans([s4_lid_x, -w / 4, s4_lid_z], lid_ellipsoid)
    c1_lid_x = 0.38 * l
    c1_lid_z = -h * c1_lid_x / (2 * l) + h / 2
    # cylinder in the front corner
    c1_lid = trans([c1_lid_x, 0, c1_lid_z], lid_cylinder)
    c3_lid_x = 0.78 * l
    c3_lid_z = -h * c3_lid_x / (2 * l) + h / 2
    c3_lid = trans([c3_lid_x, 0.17*w, c3_lid_z], lid_cylinder)
    c4_lid_x = 0.78 * l
    c4_lid_z = -h * c4_lid_x / (2 * l) + h / 2
    c4_lid = trans([c4_lid_x, -0.17*w , c4_lid_z], lid_cylinder)
    pry_space_h = r
    pry_space_r = 4*r
    pry_space_x = 0.75 * l
    pry_space_z = -h * pry_space_x / (2 * l) + h/2 + pry_space_h + 0.17
    pry_space = trans([pry_space_x, 0, pry_space_z],
                        rot([0,theta,0], (cylinder(r=pry_space_r, h=pry_space_h, center=True))))
    lid = up(r*0.8)(hull()(s1_lid, s3_lid, s4_lid))
    top_hole = lid + pry_space
    top_through_hole = (up(r*0.5)(hull()(c1_lid, c3_lid, c4_lid)))
    # all that for a stupid lid


    truss_l = 90
    truss_h = 2 * WeaponMotor.r + 8
    truss_t = WeaponMotor.base_l + 5
    weapon_motor_mount_t = WeaponMotor.base_l + 5
    weapon_motor_mount_h = 2 * WeaponMotor.r + 8
    test_truss = truss = rotate([0, 0, 0])(
        square([truss_h, truss_l])
        + translate([truss_h / 2, truss_l])(circle(truss_h / 2))
        + translate([-truss_h / 2, 0, 0])(
            rotate([0, 0, -16])((square([truss_h / 7, truss_l]))))
        + translate([truss_h + truss_h / 2, 0, 0])(
            mirror([1, 0, 0])(rotate([0, 0, -16])((square([truss_h / 7, truss_l])))))
        - translate([12.5, 10, 0])(make_triangles(r=2, l=9, num_x=2, num_y=9))

    )
    truss = rotate([0, 0, 90])(
        square([truss_h, truss_l])
        + translate([truss_h / 2, truss_l])(circle(truss_h / 2))
        - translate([12.5, 10, 0])(make_triangles(r=2, l=9, num_x=2, num_y=9)))

    truss = (rotate([90, 0, 0])(linear_extrude(height=truss_t, scale=1)(truss))
             + translate([-truss_l, -0.6*truss_t, 0])(cube([truss_l, truss_t / 4, truss_h])))

    weapon_motor_mount = translate([-overhang, 14.2, 0])(
        rotate([90, 0, 0])(
            cylinder(WeaponMotor.r + 4, weapon_motor_mount_t, center=True)) \
        + translate([truss_l, truss_t / 2, -truss_h / 2])(truss)
        - rotate([90, 0, 0])(
            cylinder(r1=WeaponMotor.base_r, r2=WeaponMotor.r, h=(WeaponMotor.base_l + 5) / 2))
        - rotate([90, 0, 0])(
            cylinder(r1=WeaponMotor.shaft_r*2, r2=WeaponMotor.shaft_r*2, h=truss_t+1, center=True))
    )

    wire_hole = translate([-5, WeaponMotor.base_l + 2, -6])(cube([40, 6, 12]))

    weapon_shaft_mount = translate([-overhang, -23, 0])(
        rotate([90, 0, 0])(
            cylinder(0.8 * (WeaponMotor.r + 4), truss_t*0.8, center=True)) \
        + (scale([0.8, 0.8, 0.8])(translate([truss_l, truss_t / 2, -truss_h / 2])(truss))))

    brace = right(l / 4)(cube([t, 0.29 * w, 0.78 * h], center=True))

    side_wall_angle = 90 - degrees(atan(l/(w/2)))
    drive_motor_mount_disp = [l * .90, w * -0.255, 0]
    drive_motor_mounts = mirror_copy(
        [0, 1, 0], trans(drive_motor_mount_disp, (rot([90, 90, -side_wall_angle], DriveSystem.mount))))
    drive_motors = mirror_copy(
        [0, 1, 0], trans(drive_motor_mount_disp, (rot([90, 90, -side_wall_angle], DriveSystem.gear_motor))))

    obj = difference()(
        union()(tetrahedron, weapon_shaft_mount, weapon_motor_mount),
        union()(tetrahedron_hole, (left(overhang)(WeaponMotor.obj))),

    )
    obj = obj + brace - wire_hole - top_hole - spinner_zone - top_through_hole + drive_motor_mounts - drive_motors





def cutaway_xz(obj: OpenSCADObject, y=0):
    return obj * translate([-5000, y, -5000])((cube(10000)))


def cutaway_xy(obj: OpenSCADObject, z=0):
    return obj * translate([-5000, -5000, z - 10000])((cube(10000)))


# what shows up
def assembly():
    #return (DriveSystem.obj + right(22)(DriveSystem.mount))
    '''return (union()(
        Frame.obj,
        mirror_copy(
            [0, 1, 0], trans(Frame.drive_motor_mount_disp, (rot([90, 90, -Frame.side_wall_angle], DriveSystem.obj))))
    ))
    '''



    #return  cutaway_xy(Frame.obj)
    # return cutaway_xz(Frame.obj + trans([Frame.l*0.8,0,0], DriveSystem.obj))

    #return WeaponMotor.obj
    return rot([0, Frame.theta, 0], Frame.obj)
    #return rot([0,Frame.theta,0], left(Frame.overhang)(WeaponMotor.obj+WeaponBlade.obj) + Frame.obj)


if __name__ == '__main__':
    scad_render_to_file(assembly(), file_header='$fn = %s;' % SEGMENTS, include_orig_code=True)
