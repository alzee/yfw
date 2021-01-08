alter table drug add sn varchar(50) default null after drugId;
alter table drug add approvalNum varchar(50) default null after sn;
