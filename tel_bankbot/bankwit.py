from wit import Wit

access_token = 'GRQ6WSEKQV7UJE6HE54D44M7JHFSMRHV'

def first_entity_value(entities, entity):
    if entity not in entities:
        return None
    val = entities[entity][0]['value']
    if not val:
        return None
    return val['value'] if isinstance(val, dict) else val


def say(session_id, context, msg):
    print(msg)

def merge(session_id, context, entities, msg):
    loc = first_entity_value(entities, 'amount_of_money')
    if loc:
        context['amount'] = loc
    exp = first_entity_value(entities, 'expense')
    if exp:
        context['expense'] = exp
    mem = first_entity_value(entities, 'contact')
    if mem:
        context['participants'] = mem
    return context


def error(session_id, context, e):
    print(str(e))

actions = {
    'say': say,
    'merge': merge,
    'error': error,
}
client = Wit(access_token, actions)

session_id = 'my-user-id-42'

def Parse(msg):
    context1 = client.run_actions(session_id, msg, {})
    print('The session state is now: ' + str(context1))
    return context1
