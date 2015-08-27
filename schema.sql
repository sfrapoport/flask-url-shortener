drop table if exists urls;

create table urls (
    shortenedurl text primary key,
    fullurl text not null,
    lookups int
);
