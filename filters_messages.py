def filter_message_for_delete(message):
    parts = message.text.split(' ')
    if len(parts) == 2 and parts[0] == 'del':
        return True


def filter_message_for_search(message):
    parts = message.text.split(' ')
    if len(parts) == 2 and parts[0] == 'date':
        return True


def filter_message_for_add(message):
    if message.text.split(' ')[0] == 'add':
        return True
