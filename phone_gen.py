import json
from event.phone_data_gen import *

file_path = 'data/'
start_time = '2025-01-01'
end_time = '2025-03-30'
persona = read_json_file(file_path+'persona.json')


contact = contact_gen(persona)
contact = remove_json_wrapper(contact)
persona = json.loads(persona)
extool.load_from_json(read_json_file(file_path+'event_update.json'),persona)
for i in iterate_dates(start_time,end_time):
    phone_gen(i,contact)