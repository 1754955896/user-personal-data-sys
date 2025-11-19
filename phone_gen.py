import json
import os.path

from event.phone_data_gen import *

file_path = 'data/'
start_time = '2025-01-01'
end_time = '2025-03-30'
persona = read_json_file(file_path+'persona.json')

contact = {}
if os.path.exists(file_path + "phone_data/contact.json"):
    contact = read_json_file(file_path + "phone_data/contact.json")
else:
    contact = contact_gen(persona)
    contact = remove_json_wrapper(contact)
    contact = json.loads(contact)
    with open(file_path + "phone_data/contact.json", "w", encoding="utf-8") as f:
        json.dump(contact, f, ensure_ascii=False, indent=2)

a = []
b = []
c = []
d = []
if os.path.exists(file_path + "phone_data/event_gallery.json"):
    a = read_json_file(file_path + "phone_data/event_gallery.json")
if os.path.exists(file_path + "phone_data/event_push.json"):
    b = read_json_file(file_path + "phone_data/event_push.json")
if os.path.exists(file_path + "phone_data/event_call.json"):
    c = read_json_file(file_path + "phone_data/event_call.json")
if os.path.exists(file_path + "phone_data/event_note.json"):
    d = read_json_file(file_path + "phone_data/event_note.json")
extool.load_from_json(read_json_file(file_path+'event_update.json'),persona)
for i in iterate_dates(start_time,end_time):
    phone_gen(i,contact,file_path,a,b,c,d)