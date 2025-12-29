CREATE TABLE `auditactiontype` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `auditlogs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userId` bigint NOT NULL,
  `affectedUsers` varchar(500) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `actionType` int NOT NULL,
  `actionNote` varchar(850) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `actionDate` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `id` (`id`),
  KEY `userId` (`userId`),
  KEY `actionType` (`actionType`),
  CONSTRAINT `auditlogs_ibfk_1` FOREIGN KEY (`actionType`) REFERENCES `auditactiontype` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `bosses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `imageUrl` varchar(250) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=39 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `channels` (
  `id` bigint NOT NULL,
  `name` varchar(60) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `drops` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `value` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=202 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `personalbests` (
  `submitterUserId` bigint NOT NULL,
  `members` varchar(650) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `status` int NOT NULL,
  `bossId` int NOT NULL,
  `scale` int NOT NULL,
  `time` varchar(6) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `submittedDate` datetime NOT NULL,
  `reviewedBy` bigint DEFAULT NULL,
  `reviewedDate` datetime DEFAULT NULL,
  `reviewNote` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  KEY `u_uid` (`submitterUserId`),
  KEY `sub_date` (`submittedDate`),
  KEY `bossId` (`bossId`),
  KEY `reviewedBy` (`reviewedBy`),
  CONSTRAINT `personalbests_ibfk_1` FOREIGN KEY (`submitterUserId`) REFERENCES `users` (`userId`) ON DELETE RESTRICT,
  CONSTRAINT `personalbests_ibfk_2` FOREIGN KEY (`bossId`) REFERENCES `bosses` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `personalbests_ibfk_3` FOREIGN KEY (`reviewedBy`) REFERENCES `users` (`userId`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pets` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  `value` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `pointtracker` (
  `Id` int NOT NULL AUTO_INCREMENT,
  `userId` bigint NOT NULL,
  `points` int NOT NULL,
  `notes` varchar(500) DEFAULT NULL,
  `dropId` int DEFAULT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY (`Id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `ranks` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `pointRequirement` int DEFAULT NULL,
  `diaryPointRequirement` int DEFAULT NULL,
  `masterDiaryRequirement` int DEFAULT NULL,
  `isStaff` bit(1) NOT NULL DEFAULT b'0',
  `discordRoleId` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `discordRoleId` (`discordRoleId`)
) ENGINE=InnoDB AUTO_INCREMENT=774 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `referrals` (
  `userId` bigint NOT NULL,
  `referrerId` bigint NOT NULL,
  UNIQUE KEY `userId` (`userId`),
  KEY `u_uid` (`userId`),
  KEY `referrerId` (`referrerId`),
  CONSTRAINT `referrals_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE RESTRICT,
  CONSTRAINT `referrals_ibfk_2` FOREIGN KEY (`referrerId`) REFERENCES `users` (`userId`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `roles` (
  `name` varchar(50) NOT NULL,
  `discordRoleId` bigint DEFAULT NULL,
  `acceptDrops` bit(1) DEFAULT b'0',
  `adminCommands` bit(1) DEFAULT b'0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `submissions` (
  `Id` int NOT NULL AUTO_INCREMENT,
  `userId` bigint NOT NULL,
  `typeId` int NOT NULL,
  `status` int NOT NULL,
  `participants` varchar(850) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `value` int DEFAULT NULL,
  `imageUrl` varchar(120) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `notes` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  `submittedDate` datetime NOT NULL,
  `reviewedBy` bigint DEFAULT NULL,
  `reviewedDate` datetime DEFAULT NULL,
  `reviewNote` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `u_uid` (`userId`),
  KEY `sub_date` (`submittedDate`),
  KEY `typeId` (`typeId`),
  KEY `reviewedBy` (`reviewedBy`),
  KEY `submissions_FK` (`status`),
  CONSTRAINT `submissions_FK` FOREIGN KEY (`status`) REFERENCES `submissionstatus` (`id`),
  CONSTRAINT `submissions_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE RESTRICT,
  CONSTRAINT `submissions_ibfk_2` FOREIGN KEY (`typeId`) REFERENCES `submissiontype` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `submissions_ibfk_3` FOREIGN KEY (`status`) REFERENCES `submissionstatus` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `submissions_ibfk_4` FOREIGN KEY (`reviewedBy`) REFERENCES `users` (`userId`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=42 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `submissionstatus` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `submissiontype` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `users` (
  `userId` bigint NOT NULL,
  `displayName` varchar(32) NOT NULL,
  `mainRSN` varchar(12) DEFAULT NULL,
  `altRSN` varchar(12) DEFAULT NULL,
  `rankId` int NOT NULL,
  `points` int unsigned NOT NULL,
  `isActive` bit(1) NOT NULL DEFAULT b'0',
  `joinDate` date DEFAULT NULL,
  `leaveDate` date DEFAULT NULL,
  `referredBy` bigint DEFAULT NULL,
  `birthday` varchar(5) CHARACTER SET utf8 COLLATE utf8_general_ci DEFAULT NULL,
  PRIMARY KEY (`userId`),
  KEY `u_uid` (`userId`),
  KEY `rankId` (`rankId`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`rankId`) REFERENCES `ranks` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
