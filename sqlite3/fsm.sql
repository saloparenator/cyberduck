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