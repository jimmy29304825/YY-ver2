CREATE SCHEMA IF NOT EXISTS yyostech_2 DEFAULT CHARACTER SET utf8mb4 ;
USE yyostech_2;
CREATE USER 'yy_raspi'@'192.168.50.87' IDENTIFIED BY 'yyraspi';
GRANT ALL PRIVILEGES ON yyostech_2.* TO 'yy_raspi'@'192.168.50.87';
FLUSH PRIVILEGES;
/*
select * from customer;
select * from demands;
select * from series;
select * from color;
select * from crop_name;
select * from supplier;
select * from crop_parameters;
select * from crop_schedule;
*/

/*作物顏色*/
CREATE TABLE IF NOT EXISTS `color` (
    `col_id` VARCHAR(1) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`col_id`)
);

/*客戶資訊*/
CREATE TABLE IF NOT EXISTS `customer` (
    `cust_id` VARCHAR(1) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`cust_id`)
);

/*科屬別*/
CREATE TABLE IF NOT EXISTS `series` (
    `series_id` VARCHAR(1) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`series_id`)
);

/*需求類型*/
CREATE TABLE IF NOT EXISTS `demands` (
    `demands_id` VARCHAR(1) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`demands_id`)
);

/*種子供應商*/
CREATE TABLE IF NOT EXISTS `supplier` (
    `supplier_id` VARCHAR(1) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`supplier_id`)
);

/*作物名稱(科屬別+顏色)*/
CREATE TABLE IF NOT EXISTS `crop_name` (
    `crop_id` VARCHAR(3) NOT NULL,
    `series_id` VARCHAR(1) NOT NULL,
    `col_id` VARCHAR(1) NOT NULL,
    `name` VARCHAR(100) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`crop_id`),
    KEY `series_idx` (`series_id`),
    KEY `col_idx` (`col_id`),
    KEY `build_datetimex` (`build_datetime`),
    CONSTRAINT `col_crop` FOREIGN KEY (`col_id`)
        REFERENCES `color` (`col_id`),
    CONSTRAINT `ser_crop` FOREIGN KEY (`series_id`)
        REFERENCES `series` (`series_id`)
);

/*品種辨識、補料參數(需求類型+作物名稱+供應商)*/
CREATE TABLE IF NOT EXISTS `crop_parameters` (
    `uid` INT(11) NOT NULL AUTO_INCREMENT,
    `demands_id` VARCHAR(1) NOT NULL,
    `crop_id` VARCHAR(3) NOT NULL,
    `supplier_id` VARCHAR(1) NOT NULL,
    `build_datetime` DATETIME NOT NULL,
    `nursery_rate` FLOAT NOT NULL,
    `Thinning_rate` FLOAT NOT NULL,
    `cultivation_rate` FLOAT NOT NULL,
    `weight` FLOAT NOT NULL,
    `thresholds` INT NOT NULL,
    `identify_value` FLOAT NOT NULL,
    PRIMARY KEY (`uid`),
    KEY `demands_idx` (`demands_id`),
    KEY `crop_idx` (`crop_id`),
    KEY `supplier_idx` (`supplier_id`),
    KEY `build_datetimex` (`build_datetime`),
    CONSTRAINT `demands_parameters` FOREIGN KEY (`demands_id`)
        REFERENCES `demands` (`demands_id`),
    CONSTRAINT `cropName_parameters` FOREIGN KEY (`crop_id`)
        REFERENCES `crop_name` (`crop_id`),
    CONSTRAINT `supplier_parameters` FOREIGN KEY (`supplier_id`)
        REFERENCES `supplier` (`supplier_id`)
);

/*生產排程(客戶+需求類型+作物名稱+供應商)*/
CREATE TABLE IF NOT EXISTS `crop_schedule` (
    `schedule_id` VARCHAR(9) NOT NULL,
    `cust_id` VARCHAR(1) NOT NULL,
    `demands_id` VARCHAR(1) NOT NULL,
    `crop_id` VARCHAR(3) NOT NULL,
    `supplier_id` VARCHAR(1) NOT NULL,
    `sowing_date` DATE NOT NULL,
    `require_date` DATE NOT NULL,
    PRIMARY KEY (`schedule_id`),
    KEY `cust_idx` (`cust_id`),
    KEY `demands_idx` (`demands_id`),
    KEY `crop_idx` (`crop_id`),
    KEY `supplier_idx` (`supplier_id`),
    KEY `sowing_datex` (`sowing_date`),
    CONSTRAINT `cust_schedule` FOREIGN KEY (`cust_id`)
        REFERENCES `customer` (`cust_id`),
    CONSTRAINT `demands_schedule` FOREIGN KEY (`demands_id`)
        REFERENCES `demands` (`demands_id`),
    CONSTRAINT `cropName_schedule` FOREIGN KEY (`crop_id`)
        REFERENCES `crop_name` (`crop_id`),
    CONSTRAINT `supplier_schedule` FOREIGN KEY (`supplier_id`)
        REFERENCES `supplier` (`supplier_id`)
);

/*樹莓派照片*/
CREATE TABLE IF NOT EXISTS `raspi_image` (
    `image_id` VARCHAR(38) NOT NULL,
    `image` LONGBLOB NOT NULL,
    `create_datetime` DATETIME NOT NULL,
    PRIMARY KEY (`image_id`)
);
  
/*拍攝流程(樹莓派照片+生產排程)*/
CREATE TABLE IF NOT EXISTS `process` (
    `process_id` VARCHAR(40) NOT NULL,
    `schedule_id` VARCHAR(9) NOT NULL,
    `image_id` VARCHAR(38) NOT NULL,
    `piece` INT NOT NULL,
    `germination_cnt` INT NOT NULL,
    PRIMARY KEY (`process_id`),
    INDEX `schedule_idx` (`schedule_id` ASC),
    CONSTRAINT `schedule_process` FOREIGN KEY (`schedule_id`)
        REFERENCES `crop_schedule` (`schedule_id`),
    CONSTRAINT `image_process` FOREIGN KEY (`image_id`)
        REFERENCES `raspi_image` (`image_id`)
);
    
/*海綿資訊(拍攝流程)*/
CREATE TABLE IF NOT EXISTS `sponge` (
    `sponge_id` INT(11) NOT NULL AUTO_INCREMENT,
    `process_id` VARCHAR(40) NOT NULL,
    `crop_percentage` FLOAT NOT NULL,
    `is_germinate` TINYINT(1) NOT NULL,
    `position_x` INT NOT NULL,
    `position_y` INT NOT NULL,
    `sp_image` LONGBLOB NOT NULL,
    PRIMARY KEY (`sponge_id`),
    INDEX `process_idx` (`process_id`),
    CONSTRAINT `process_sponge` FOREIGN KEY (`process_id`)
        REFERENCES `process` (`process_id`)
);

/*人工判斷紀錄(海綿資訊)*/
CREATE TABLE IF NOT EXISTS `artificial_judgment` (
    `judge_id` INT(11) NOT NULL AUTO_INCREMENT,
    `sponge_id` INT(11) NOT NULL,
    `create_datetime` DATETIME NOT NULL,
    `judge_result` TINYINT(1) NOT NULL,
    PRIMARY KEY (`judge_id`),
    INDEX `sponge_idx` (`sponge_id`),
    CONSTRAINT `sponge_artificial` FOREIGN KEY (`sponge_id`)
        REFERENCES `sponge` (`sponge_id`)
);