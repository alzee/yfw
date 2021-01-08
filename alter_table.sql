alter table drug add if not exists sn varchar(50) default null after drugId;
alter table drug add if not exists approvalNum varchar(50) default null after sn;
alter table drug add if not exists priceMin2 varchar(50) default null after priceMin;
