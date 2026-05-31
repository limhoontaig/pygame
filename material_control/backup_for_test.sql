-- --------------------------------------------------------
-- 호스트:                          127.0.0.1
-- 서버 버전:                        12.3.2-MariaDB - MariaDB Server
-- 서버 OS:                        Win64
-- HeidiSQL 버전:                  12.17.0.7270
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- inventory_db 데이터베이스 구조 내보내기
CREATE DATABASE IF NOT EXISTS `inventory_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_uca1400_ai_ci */;
USE `inventory_db`;

-- 테이블 inventory_db.dongho_master 구조 내보내기
CREATE TABLE IF NOT EXISTS `dongho_master` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dong` varchar(20) NOT NULL,
  `ho` varchar(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `dong` (`dong`,`ho`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 테이블 데이터 inventory_db.dongho_master:~0 rows (대략적) 내보내기

-- 테이블 inventory_db.inbound_ledger 구조 내보내기
CREATE TABLE IF NOT EXISTS `inbound_ledger` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `in_date` varchar(20) NOT NULL,
  `discipline` varchar(50) DEFAULT NULL,
  `item_name` varchar(200) NOT NULL,
  `spec` varchar(200) DEFAULT NULL,
  `qty` int(11) DEFAULT 0,
  `total_price` int(11) DEFAULT 0,
  `unit_price` int(11) DEFAULT 0,
  `supplier` varchar(100) DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `worker` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 테이블 데이터 inventory_db.inbound_ledger:~0 rows (대략적) 내보내기
INSERT IGNORE INTO `inbound_ledger` (`id`, `in_date`, `discipline`, `item_name`, `spec`, `qty`, `total_price`, `unit_price`, `supplier`, `remarks`, `worker`, `created_at`) VALUES
	(1, '2026-05-31', '전기', '전등', 'led 10', 100, 1000, 10, '', '', 'admin', '2026-05-31 10:58:40'),
	(2, '2026-05-31', '기계', '전동차', '10마력', 2, 10000000, 5000000, '', '', 'admin', '2026-05-31 10:59:25'),
	(3, '2026-05-31', '소방', '감지기', '정온식', 100, 589000, 5890, '', '', 'admin', '2026-05-31 11:00:30');

-- 테이블 inventory_db.material_items 구조 내보내기
CREATE TABLE IF NOT EXISTS `material_items` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `item_name` varchar(200) NOT NULL,
  `spec` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `item_name` (`item_name`,`spec`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 테이블 데이터 inventory_db.material_items:~0 rows (대략적) 내보내기
INSERT IGNORE INTO `material_items` (`id`, `item_name`, `spec`) VALUES
	(1, '전등', 'led 10'),
	(2, '전동차', '10마력'),
	(3, '감지기', '정온식');

-- 테이블 inventory_db.usage_ledger 구조 내보내기
CREATE TABLE IF NOT EXISTS `usage_ledger` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `use_date` varchar(20) NOT NULL,
  `usage_type` varchar(50) NOT NULL,
  `dong` varchar(20) DEFAULT NULL,
  `ho` varchar(20) DEFAULT NULL,
  `discipline` varchar(50) DEFAULT NULL,
  `item_name` varchar(200) NOT NULL,
  `spec` varchar(200) DEFAULT NULL,
  `qty` int(11) DEFAULT 0,
  `remarks` text DEFAULT NULL,
  `worker` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 테이블 데이터 inventory_db.usage_ledger:~0 rows (대략적) 내보내기

-- 테이블 inventory_db.users 구조 내보내기
CREATE TABLE IF NOT EXISTS `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `status` varchar(20) DEFAULT 'PENDING',
  `is_admin` int(11) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

-- 테이블 데이터 inventory_db.users:~1 rows (대략적) 내보내기
INSERT IGNORE INTO `users` (`id`, `username`, `password`, `status`, `is_admin`, `created_at`) VALUES
	(1, 'admin', 'ac9689e2272427085e35b9d3e3e8bed88cb3434828b43b86fc0596cad4c6e270', 'APPROVED', 1, '2026-05-31 10:15:32');

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
