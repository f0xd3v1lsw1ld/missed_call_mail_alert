--schema for calllist application

create table contacts (   
    number text primary key,
    name text,
    UNIQUE(number)
);

create table calllist (
    date_time date,
    number text,
    port text,
    duration integer,
    notification boolean default 0,
    UNIQUE(date_time)
);