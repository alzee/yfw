alter table drug add if not exists sn varchar(50) default null after drugId;
alter table drug add if not exists approvalNum varchar(50) default null after sn;
alter table drug add if not exists priceMin2 varchar(50) default null after priceMin;
alter table drug add if not exists updateOn timestamp not null default current_timestamp on update current_timestamp;
alter table drug add if not exists ourStock varchar(50) default null after ourPrice;
alter table drug add if not exists stockPriceMin varchar(50) default null after priceMin;
alter table drug add if not exists stockPriceMin2 varchar(50) default null after priceMin2;
