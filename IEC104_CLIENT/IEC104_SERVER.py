# -*- coding: utf-8 -*-

from encodings import utf_8
import imp
from platform import python_version
from wsgiref.simple_server import sys_version
import c104

print("Hello world!");

a = 50;
slavek = "slavek";

print("Toto je moje prvni aplikace v Pythonu.");

print("Verze pythonu: " + sys_version);

print(type(a), type(slavek));
print(type(sys_version));