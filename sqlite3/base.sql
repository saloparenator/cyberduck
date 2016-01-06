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
INSERT INTO action VALUES(0,NULL,0,0,'0');

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
        INNER JOIN context ON context.id = action.context_id
        WHERE last_action_id IS NOT NULL;

CREATE VIEW IF NOT EXISTS view_last_action AS
        SELECT action_id,
               last_action_id,
               event_id,
               event_name,
               context_id,
               context_name,
               timestamp
        FROM view_action
        GROUP BY context_id
        ORDER BY timestamp DESC;

CREATE VIEW IF NOT EXISTS view_build_action AS
        SELECT last.action_id AS last_action_id, 
               last.context_id AS context_id, 
               event.id AS event_id, 
               last.context_name AS context_name, 
               event.name AS event_name
        FROM view_last_action AS last
        CROSS JOIN event;
/*
USE CASE
emit an action
    INSERT INTO action (last_action_id, context_id, event_id)
    SELECT last.action_id, last.context_id, event.id
    FROM view_last_action AS last
    INNER JOIN event ON event_name = '... name of the event ...'
    WHERE context_name = '... name of the context ...'
*/