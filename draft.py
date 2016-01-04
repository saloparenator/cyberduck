import sqlite3

_init_sql = """
PRAGMA foreign_keys = ON;

/*
multiple execution instance per machine
all machine/instance processed at the same time
event are bound to a scope, maybe using user/group
should use log based event execution system, so every thing is recoverable
execution should be called with only one event per cycle

 _order_
|       |?
|   [action]    [event]
|__n|      |1__n|     |
    |______|    |_____|
       |1
       |n
    [context]
    |       |
    |_______|
*/

CREATE TABLE IF NOT EXISTS event(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO event VALUES(0,'begin');

CREATE TABLE IF NOT EXISTS context(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO context VALUES(0,'void');

CREATE TABLE IF NOT EXISTS action(
    id INTEGER PRIMARY KEY,
    last_action_id INTEGER REFERENCES action(id) NULL,
    event_id INTEGER REFERENCES event(id) NOT NULL,
    context_id INTEGER REFERENCES context(id) NOT NULL,
    timestamp NUMERIC DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO action VALUES(0,NULL,0,0,CURRENT_TIMESTAMP);

CREATE VIEW IF NOT EXISTS view_action AS
        SELECT action.id AS action_id,
               last_action_id,
               event.id AS event_id,
               event.name AS event_name,
               context.id AS context_id,
               context.name AS context_name,
               timestamp
        FROM action
        INNER JOIN event ON event.id = action.event_id
        INNER JOIN context ON context.id = action.context_id;
/*

 [action]
 |  :)  |
 |______|
    |n
    |
    |1
[instance]   [event]
|        |   |  :) |
|________|   |_____|
    |1          |n
    |           |
    |n          |1
 [ fsm ]   [transition]
 |     |n_1|          |
 |_____|   |__________|
    |1          |2
    |           |
    |           |n
    |        [state]
    |_______n|     |
             |_____|
*/

CREATE TABLE IF NOT EXISTS fsm_state(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fsm_machine(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    first_state_id INTEGER REFERENCES fsm_state(id) NOT NULL
);

CREATE TABLE IF NOT EXISTS fsm_transition(
    id INTEGER PRIMARY KEY,
    machine_id INTEGER REFERENCES fsm_machine(id) NOT NULL,
    event_id INTEGER REFERENCES event(id) NOT NULL,
    from_state_id INTEGER REFERENCES fsm_state(id) NOT NULL,
    next_state_id INTEGER REFERENCES fsm_state(id) NOT NULL
);

CREATE TABLE IF NOT EXISTS fsm_instance(
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    machine_id INTEGER     REFERENCES fsm_machine(id) NOT NULL,
    last_action_id INTEGER REFERENCES action(id)      NOT NULL,
    state_id INTEGER       REFERENCES fsm_state(id)   NOT NULL
);

CREATE VIEW IF NOT EXISTS fsm_view_transition AS
    SELECT fsm_state.id              AS state_id,
           fsm_state.name            AS state_name,
           fsm_machine.id            AS machine_id,
           fsm_machine.name          AS machine_name,
           fsm_transition.id         AS transition_id,
           COALESCE(event.id,NULL)   AS event_id,
           COALESCE(event.name,NULL) AS event_name,
           next_state.id             AS next_state_id,
           next_state.name           AS next_state_name
    FROM fsm_transition
    INNER JOIN fsm_state               ON fsm_transition.from_state_id = fsm_state.id
    INNER JOIN event                   ON fsm_transition.event_id      = event.id
    INNER JOIN fsm_machine             ON fsm_machine.id               = fsm_transition.machine_id
    INNER JOIN fsm_state AS next_state ON next_state.id                = fsm_transition.next_state_id;

CREATE VIEW IF NOT EXISTS fsm_view_instance AS
    SELECT fsm_instance.id   AS instance_id,
           fsm_instance.name AS instance_name,
           fsm_machine.id    AS machine_id,
           fsm_machine.name  AS machine_name,
           fsm_state.id      AS state_id,
           fsm_state.name    AS state_name,
           last_action_id
    FROM fsm_instance
    INNER JOIN fsm_machine ON fsm_machine.id = fsm_instance.machine_id
    INNER JOIN fsm_state   ON fsm_state.id   = fsm_instance.state_id;

/*
new instance
usage:
INSERT INTO fsm_instance(name,machine_id,last_action_id,state_id)
SELECT name,machine_id,last_action_id,state_id
FROM fsm_init_view_instance
WHERE fsm_name = '...fsm machine name...'

usage:
INSERT INTO fsm_instance(name,machine_id,last_action_id,state_id)
SELECT '... name of this instance ...',machine_id,last_action_id,state_id
FROM fsm_init_view_instance
WHERE fsm_name = '...fsm machine name...'
*/
CREATE VIEW IF NOT EXISTS fsm_init_view_instance AS
    SELECT NULL AS id,
           'began:' || CURRENT_TIMESTAMP AS name,
           fsm_machine.id AS machine_id,
           0 AS last_action_id,
           fsm_state.id AS state_id,
           fsm_machine.name AS machine_name
    FROM fsm_machine
    INNER JOIN fsm_state ON fsm_machine.first_state_id = fsm_state.id;

/*
next turn
usage:
UPDATE fsm_instance SET
    last_action_id=(SELECT
*/
CREATE VIEW IF NOT EXISTS fsm_turn_view_instance AS
    SELECT instance.instance_id AS id,
           instance.instance_name AS name,
           instance.machine_id AS machine_id,
           action.action_id AS last_action_id,
           transition.next_state_id AS state_id
    FROM view_action AS action
    INNER JOIN fsm_view_instance AS instance ON action.last_action_id = instance.last_action_id
    INNER JOIN fsm_view_transition AS transition ON transition.machine_id = instance.machine_id
    WHERE transition.event_id = action.event_id
    AND transition.state_id = instance.state_id;

/*
query
return list of props, though fsm instance only have one value to expose, it will yield as a list containing one value
*/
"""

#example
#from https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Turnstile_state_machine_colored.svg/330px-Turnstile_state_machine_colored.svg.png
_test_sql = """
INSERT INTO context(id,name)                                      VALUES(1,'turnstileA');
INSERT INTO event(id,name)                                        VALUES(1,'push');
INSERT INTO event(id,name)                                        VALUES(2,'coin');
INSERT INTO fsm_state(id,name)                                    VALUES(1,'locked');
INSERT INTO fsm_state(id,name)                                    VALUES(2,'unlocked');
INSERT INTO fsm_machine(id,name,first_state_id)                   VALUES(1,'turnstile',1);
INSERT INTO fsm_transition                                        VALUES(1,1,1,1,1);
INSERT INTO fsm_transition                                        VALUES(2,1,2,1,2);
INSERT INTO fsm_transition                                        VALUES(3,1,1,2,1);
INSERT INTO fsm_transition                                        VALUES(4,1,2,2,2);
INSERT INTO action (id,last_action_id,event_id,context_id)        VALUES(1,0,1,1);
INSERT INTO fsm_instance (id,name,machine_id,state_id,last_action_id) VALUES(1,'turnstileA',1,1,0);
"""
_test_json = {
        'name' : "turnstile",
        'type' : "fsm",
        'begin' : "locked",
        'state' : [
                "locked",
                "unlocked"
        ],
        'transition' : [
                {
                        'event' : "push",
                        'from' : "locked",
                        'next' : "locked"
                },
                {
                        'event' : "coin",
                        'from' : "locked",
                        'next' : "unlocked"
                },
                {
                        'event' : "push",
                        'from' : "unlocked",
                        'next' : "locked"
                },
                {
                        'event' : "coin",
                        'from' : "unlocked",
                        'next' : "unlocked"
                }
        ]
}

def InitDatabase(conn):
    '''
    >>> conn = sqlite3.connect(':memory:')
    >>> c = conn.executescript(_init_sql)
    >>> c = conn.executescript(_test_sql)
    >>> conn.commit()
    >>> cur = conn.cursor()

    >>> query = "SELECT * FROM fsm_init_view_instance WHERE machine_name='turnstile'"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> for _id,_name,_machine_id,_last_action_id,_state_id,_ in result:
    ...     if not _id == None:          print('id should be 1 but was %s'                % _id)
    ...     if not 'began:' in _name:    print('_name should contain "began:" but was %s' % _name)
    ...     if not _machine_id == 1:     print('_machine_id should be 1 but was %s'       % _machine_id)
    ...     if not _last_action_id == 0: print('_last_action_id should be 0 but was %s'   % _last_action_id)
    ...     if not _state_id == 1:       print('_state_id should be 1 but was %s'         % _state_id)

    >>> query = "SELECT * FROM fsm_turn_view_instance"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(1, u'turnstileA', 1, 1, 1)]

    >>> query = "SELECT * FROM fsm_view_instance"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    '''
    if not conn:
        conn = sqlite3.connect(':memory:')
    c = conn.executescript(_init_sql)
    conn.commit()
    return conn

def NewInstance(conn,MachineName,InstanceName=None):
    cur = conn.cursor()
    if not InstanceName:
        cur.execute("""
                INSERT INTO fsm_instance(name,machine_id,last_action_id,state_id)
                SELECT name,machine_id,last_action_id,state_id
                FROM fsm_init_view_instance
                WHERE machine_name = '%s'
        """ % MachineName)
    else:
        cur.execute("""
                INSERT INTO fsm_instance(name,machine_id,last_action_id,state_id)
                SELECT '%s',machine_id,last_action_id,state_id
                FROM fsm_init_view_instance
                WHERE machine_name = '%s'
        """ % (InstanceName,MachineName))

    conn.commit()
    return conn

def BuildMachine(conn,FSM):
    """
    >>> conn = sqlite3.connect(':memory:')
    >>> conn = InitDatabase(conn)
    >>> conn = BuildMachine(conn,_test_json)
    >>> conn.commit()
    >>> cur = conn.cursor()
    TODO
    >>> query = "SELECT * FROM fsm_turn_view_instance"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()
    >>> print(result)
    [(1, u'turnstileA', 1, 1, 1)]

    >>> query = "SELECT * FROM fsm_view_instance"
    >>> cur = cur.execute(query)
    >>> result = cur.fetchall()

    """
    cur = conn.cursor()
    for state in FSM['state']:
        cur.execute("INSERT INTO fsm_state(name) VALUES('%s')" % state)
    cur.execute("INSERT INTO fsm_machine(name,first_state_id) SELECT '%s',id FROM fsm_state WHERE name='%s'" %
                (FSM['name'],FSM['begin']))
    for transition in FSM['transition']:
        cur.execute(""" INSERT INTO fsm_transition (event_id,from_state_id,next_state_id,machine_id)
                        SELECT event.id, from_state.id, next_state.id, fsm_machine.id
                        FROM fsm_state AS from_state, fsm_state AS next_state, event, fsm_machine
                        WHERE from_state.name='%s'
                        AND next_state.name='%s'
                        AND event.name='%s'
                        AND fsm_machine.name='%s'""" %
                        (transition['from'],transition['next'],transition['event'],FSM['name']))
    return conn



if __name__ == '__main__':
    import doctest
    doctest.testmod()

