--
-- Table structure for table `auditactiontype`
--

DROP TABLE IF EXISTS `auditactiontype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditactiontype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auditlogs`
--

DROP TABLE IF EXISTS `auditlogs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditlogs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userId` bigint(20) NOT NULL,
  `affectedUsers` varchar(1000) CHARACTER SET utf8 DEFAULT NULL,
  `actionType` int(11) NOT NULL,
  `actionNote` varchar(850) CHARACTER SET utf8 DEFAULT NULL,
  `actionDate` datetime NOT NULL,
  `posted` binary(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `id` (`id`),
  KEY `userId` (`userId`),
  KEY `auditlogs_ibfk_1` (`actionType`),
  CONSTRAINT `auditlogs_FK` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON UPDATE CASCADE,
  CONSTRAINT `auditlogs_ibfk_1` FOREIGN KEY (`actionType`) REFERENCES `auditactiontype` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=23292 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bingoWinners`
--

DROP TABLE IF EXISTS `bingoWinners`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bingoWinners` (
  `bingoId` int(11) NOT NULL AUTO_INCREMENT,
  `bingoName` varchar(100) DEFAULT NULL,
  `teamName` varchar(100) DEFAULT NULL,
  `participants` varchar(300) DEFAULT NULL,
  PRIMARY KEY (`bingoId`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bingoboard`
--

DROP TABLE IF EXISTS `bingoboard`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bingoboard` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sheetsUrl` varchar(200) DEFAULT NULL,
  `width` int(11) DEFAULT NULL,
  `height` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bingobosskc`
--

DROP TABLE IF EXISTS `bingobosskc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bingobosskc` (
  `RSN` varchar(35) NOT NULL,
  `abyssal_sire` int(11) DEFAULT '0',
  `alchemical_hydra` int(11) DEFAULT '0',
  `artio` int(11) DEFAULT '0',
  `barrows_chests` int(11) DEFAULT '0',
  `bryophyta` int(11) DEFAULT '0',
  `callisto` int(11) DEFAULT '0',
  `calvarion` int(11) DEFAULT '0',
  `cerberus` int(11) DEFAULT '0',
  `chambers_of_xeric` int(11) DEFAULT '0',
  `chambers_of_xeric_challenge_mode` int(11) DEFAULT '0',
  `chaos_elemental` int(11) DEFAULT '0',
  `chaos_fanatic` int(11) DEFAULT '0',
  `commander_zilyana` int(11) DEFAULT '0',
  `corporeal_beast` int(11) DEFAULT '0',
  `crazy_archaeologist` int(11) DEFAULT '0',
  `dagannoth_prime` int(11) DEFAULT '0',
  `dagannoth_rex` int(11) DEFAULT '0',
  `dagannoth_supreme` int(11) DEFAULT '0',
  `deranged_archaeologist` int(11) DEFAULT '0',
  `duke_sucellus` int(11) DEFAULT '0',
  `general_graardor` int(11) DEFAULT '0',
  `giant_mole` int(11) DEFAULT '0',
  `grotesque_guardians` int(11) DEFAULT '0',
  `hespori` int(11) DEFAULT '0',
  `kalphite_queen` int(11) DEFAULT '0',
  `king_black_dragon` int(11) DEFAULT '0',
  `kraken` int(11) DEFAULT '0',
  `kreearra` int(11) DEFAULT '0',
  `kril_tsutsaroth` int(11) DEFAULT '0',
  `lunar_chests` int(11) DEFAULT '0',
  `mimic` int(11) DEFAULT '0',
  `nex` int(11) DEFAULT '0',
  `nightmare` int(11) DEFAULT '0',
  `phosanis_nightmare` int(11) DEFAULT '0',
  `obor` int(11) DEFAULT '0',
  `phantom_muspah` int(11) DEFAULT '0',
  `sarachnis` int(11) DEFAULT '0',
  `scorpia` int(11) DEFAULT '0',
  `scurrius` int(11) DEFAULT '0',
  `skotizo` int(11) DEFAULT '0',
  `sol_heredit` int(11) DEFAULT '0',
  `spindel` int(11) DEFAULT '0',
  `tempoross` int(11) DEFAULT '0',
  `the_gauntlet` int(11) DEFAULT '0',
  `the_corrupted_gauntlet` int(11) DEFAULT '0',
  `the_leviathan` int(11) DEFAULT '0',
  `the_whisperer` int(11) DEFAULT '0',
  `theatre_of_blood` int(11) DEFAULT '0',
  `theatre_of_blood_hard_mode` int(11) DEFAULT '0',
  `thermonuclear_smoke_devil` int(11) DEFAULT '0',
  `tombs_of_amascut` int(11) DEFAULT '0',
  `tombs_of_amascut_expert` int(11) DEFAULT '0',
  `tzkal_zuk` int(11) DEFAULT '0',
  `tztok_jad` int(11) DEFAULT '0',
  `vardorvis` int(11) DEFAULT '0',
  `venenatis` int(11) DEFAULT '0',
  `vetion` int(11) DEFAULT '0',
  `vorkath` int(11) DEFAULT '0',
  `wintertodt` int(11) DEFAULT '0',
  `zalcano` int(11) DEFAULT '0',
  `zulrah` int(11) DEFAULT '0',
  `yama` int(11) DEFAULT NULL,
  PRIMARY KEY (`RSN`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bingodrops`
--

DROP TABLE IF EXISTS `bingodrops`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bingodrops` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(80) NOT NULL,
  `value` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3553 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bosses`
--

DROP TABLE IF EXISTS `bosses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bosses` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 NOT NULL,
  `imageUrl` varchar(250) CHARACTER SET utf8 DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=44 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `channels`
--

DROP TABLE IF EXISTS `channels`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `channels` (
  `id` bigint(20) NOT NULL,
  `name` varchar(60) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `deathTable`
--

DROP TABLE IF EXISTS `deathTable`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `deathTable` (
  `msgID` varchar(45) DEFAULT NULL,
  `time` varchar(45) DEFAULT NULL,
  `rsn` varchar(45) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diaryrewards`
--

DROP TABLE IF EXISTS `diaryrewards`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diaryrewards` (
  `diaryTier` int(11) NOT NULL,
  `points` int(11) DEFAULT NULL,
  `diaryPointsReq` int(11) DEFAULT NULL,
  PRIMARY KEY (`diaryTier`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diarytimes`
--

DROP TABLE IF EXISTS `diarytimes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diarytimes` (
  `diaryId` int(11) NOT NULL AUTO_INCREMENT,
  `bossId` int(11) NOT NULL,
  `scale` int(11) DEFAULT NULL,
  `maxDifficulty` int(11) DEFAULT NULL,
  `timeEasy` varchar(20) DEFAULT '0',
  `timeMedium` varchar(20) DEFAULT '0',
  `timeHard` varchar(20) DEFAULT '0',
  `timeElite` varchar(20) DEFAULT '0',
  `timeMaster` varchar(20) DEFAULT '0',
  PRIMARY KEY (`diaryId`),
  KEY `bosses_idx` (`bossId`),
  CONSTRAINT `bosses` FOREIGN KEY (`bossId`) REFERENCES `bosses` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=105 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `diarytypes`
--

DROP TABLE IF EXISTS `diarytypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `diarytypes` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `difficulty` int(11) NOT NULL,
  `diaryPoints` int(11) NOT NULL,
  `flavourText` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  UNIQUE KEY `diaryPoints_UNIQUE` (`diaryPoints`),
  UNIQUE KEY `difficulty_UNIQUE` (`difficulty`),
  UNIQUE KEY `flavourText_UNIQUE` (`flavourText`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `discordProfileImageUrl`
--

DROP TABLE IF EXISTS `discordProfileImageUrl`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `discordProfileImageUrl` (
  `userId` bigint(20) NOT NULL,
  `discordProfileImageUrl` varchar(345) DEFAULT NULL,
  PRIMARY KEY (`userId`),
  CONSTRAINT `foreign_key_discord_profile_userId` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `discordelo`
--

DROP TABLE IF EXISTS `discordelo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `discordelo` (
  `userId` bigint(20) NOT NULL,
  `discordElo` int(11) DEFAULT '1200',
  `discordElo2024` int(11) DEFAULT '0',
  `discordEloChange` int(11) DEFAULT '0',
  PRIMARY KEY (`userId`),
  CONSTRAINT `user_id_key` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `discordelotiers`
--

DROP TABLE IF EXISTS `discordelotiers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `discordelotiers` (
  `tier` int(11) NOT NULL,
  `tierName` varchar(45) DEFAULT NULL,
  `tierEmoji` varchar(45) DEFAULT NULL,
  `tierPointReq` int(11) DEFAULT NULL,
  PRIMARY KEY (`tier`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `drops`
--

DROP TABLE IF EXISTS `drops`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `drops` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 NOT NULL,
  `value` int(15) DEFAULT '0',
  `geValue` int(15) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=4437 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `loggedmsgs`
--

DROP TABLE IF EXISTS `loggedmsgs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `loggedmsgs` (
  `messageID` bigint(20) NOT NULL,
  `authorID` bigint(20) DEFAULT NULL,
  `messageChan` bigint(20) DEFAULT NULL,
  `guildID` bigint(20) DEFAULT NULL,
  `messageContent` varchar(1000) CHARACTER SET latin1 DEFAULT NULL,
  `datetimeMSG` datetime DEFAULT NULL,
  PRIMARY KEY (`messageID`),
  KEY `primary_index` (`datetimeMSG`,`authorID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `miscRoles`
--

DROP TABLE IF EXISTS `miscRoles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `miscRoles` (
  `roleName` varchar(100) NOT NULL,
  `userId` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `miscmodes`
--

DROP TABLE IF EXISTS `miscmodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `miscmodes` (
  `modeName` varchar(50) NOT NULL,
  `modeStatus` int(11) NOT NULL DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `new_table`
--

DROP TABLE IF EXISTS `new_table`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `new_table` (
  `userId` int(11) NOT NULL,
  `avatarHash` varchar(95) DEFAULT NULL,
  PRIMARY KEY (`userId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `personalbests`
--

DROP TABLE IF EXISTS `personalbests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personalbests` (
  `submissionId` int(11) NOT NULL AUTO_INCREMENT,
  `submitterUserId` bigint(20) NOT NULL,
  `members` varchar(650) CHARACTER SET utf8 DEFAULT NULL,
  `status` int(11) NOT NULL,
  `bossId` int(11) NOT NULL,
  `scale` int(11) NOT NULL,
  `time` varchar(20) CHARACTER SET utf8 NOT NULL,
  `imageUrl` varchar(250) DEFAULT NULL,
  `submittedDate` datetime DEFAULT NULL,
  `reviewedBy` bigint(20) DEFAULT NULL,
  `reviewedDate` datetime DEFAULT NULL,
  `reviewNote` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  PRIMARY KEY (`submissionId`),
  KEY `u_uid` (`submitterUserId`),
  KEY `sub_date` (`submittedDate`),
  KEY `personalbests_ibfk_3` (`reviewedBy`),
  KEY `personalbests_ibfk_2` (`bossId`),
  KEY `personalbests_FK` (`status`),
  CONSTRAINT `personalbests_FK` FOREIGN KEY (`status`) REFERENCES `submissionstatus` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `personalbests_ibfk_1` FOREIGN KEY (`submitterUserId`) REFERENCES `users` (`userId`) ON UPDATE CASCADE,
  CONSTRAINT `personalbests_ibfk_2` FOREIGN KEY (`bossId`) REFERENCES `bosses` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `personalbests_ibfk_3` FOREIGN KEY (`reviewedBy`) REFERENCES `users` (`userId`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18867 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `personalbests_users`
--

DROP TABLE IF EXISTS `personalbests_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personalbests_users` (
  `Id` int(11) NOT NULL,
  `userId` bigint(20) DEFAULT NULL,
  `pbId` int(11) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `userId_idx` (`userId`),
  KEY `FK_UserID_idx` (`userId`),
  KEY `FK_PBID_idx` (`pbId`),
  CONSTRAINT `FK_PBID` FOREIGN KEY (`pbId`) REFERENCES `personalbests` (`submissionId`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `FK_UserID` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pets`
--

DROP TABLE IF EXISTS `pets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 NOT NULL,
  `value` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pointtracker`
--

DROP TABLE IF EXISTS `pointtracker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pointtracker` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `userId` bigint(20) NOT NULL,
  `points` int(11) NOT NULL,
  `notes` varchar(500) DEFAULT NULL,
  `dropId` int(11) DEFAULT NULL,
  `date` datetime NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `pointtracker_FK` (`userId`),
  KEY `pointtracker_FK_1` (`dropId`),
  CONSTRAINT `pointtracker_FK` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON UPDATE CASCADE,
  CONSTRAINT `pointtracker_FK_1` FOREIGN KEY (`dropId`) REFERENCES `submissions` (`Id`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=38415 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pointtrackerOverTimeEvents`
--

DROP TABLE IF EXISTS `pointtrackerOverTimeEvents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pointtrackerOverTimeEvents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `eventName` varchar(100) DEFAULT NULL,
  `date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ranks`
--

DROP TABLE IF EXISTS `ranks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ranks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) NOT NULL,
  `pointRequirement` int(11) DEFAULT NULL,
  `diaryPointRequirement` int(11) DEFAULT '0',
  `masterDiaryRequirement` int(11) DEFAULT '0',
  `maintenancePoints` int(11) NOT NULL DEFAULT '0',
  `discordRoleId` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `discordRoleId` (`discordRoleId`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ranksgraceperiod`
--

DROP TABLE IF EXISTS `ranksgraceperiod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ranksgraceperiod` (
  `gracePeriod` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rankupdelay`
--

DROP TABLE IF EXISTS `rankupdelay`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rankupdelay` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `memberID` bigint(20) DEFAULT NULL,
  `dateDelayedFrom` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=129 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `referrals`
--

DROP TABLE IF EXISTS `referrals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `referrals` (
  `userId` bigint(20) NOT NULL,
  `referralIds` varchar(450) NOT NULL,
  UNIQUE KEY `userId` (`userId`),
  KEY `u_uid` (`userId`),
  CONSTRAINT `referrals_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `name` varchar(50) NOT NULL,
  `discordRoleId` bigint(20) DEFAULT NULL,
  `acceptDrops` bit(1) DEFAULT b'0',
  `adminCommands` bit(1) DEFAULT b'0',
  `pbAcceptor` bit(1) DEFAULT b'0',
  `hasRoleIcon` bit(1) DEFAULT b'0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submission_participants`
--

DROP TABLE IF EXISTS `submission_participants`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `submission_participants` (
  `dropId` int(11) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `userId` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `submission dropID_idx` (`dropId`),
  KEY `users userId_idx` (`userId`),
  CONSTRAINT `dropid_foreignkey` FOREIGN KEY (`dropId`) REFERENCES `submissions` (`Id`) ON DELETE NO ACTION ON UPDATE NO ACTION,
  CONSTRAINT `userid_foreignkey` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB AUTO_INCREMENT=102015 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submissions`
--

DROP TABLE IF EXISTS `submissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `submissions` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `userId` bigint(20) NOT NULL,
  `typeId` int(11) NOT NULL,
  `status` int(11) NOT NULL,
  `participants` varchar(850) CHARACTER SET utf8 DEFAULT NULL,
  `value` int(11) DEFAULT NULL,
  `imageUrl` varchar(320) CHARACTER SET utf8 DEFAULT NULL,
  `notes` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `submittedDate` datetime NOT NULL,
  `reviewedBy` bigint(20) DEFAULT NULL,
  `reviewedDate` datetime DEFAULT NULL,
  `reviewNote` varchar(100) CHARACTER SET utf8 DEFAULT NULL,
  `bingo` int(2) DEFAULT '0',
  `messageUrl` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`Id`),
  KEY `u_uid` (`userId`),
  KEY `sub_date` (`submittedDate`),
  KEY `submissions_FK_1` (`status`),
  KEY `submissions_ibfk_2` (`typeId`),
  KEY `submissions_ibfk_4` (`reviewedBy`),
  CONSTRAINT `submissions_FK` FOREIGN KEY (`status`) REFERENCES `submissionstatus` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `submissions_FK_1` FOREIGN KEY (`status`) REFERENCES `submissionstatus` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `submissions_ibfk_1` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON UPDATE CASCADE,
  CONSTRAINT `submissions_ibfk_2` FOREIGN KEY (`typeId`) REFERENCES `submissiontype` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `submissions_ibfk_4` FOREIGN KEY (`reviewedBy`) REFERENCES `users` (`userId`) ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=18724 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submissionstatus`
--

DROP TABLE IF EXISTS `submissionstatus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `submissionstatus` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `submissiontype`
--

DROP TABLE IF EXISTS `submissiontype`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `submissiontype` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) CHARACTER SET utf8 NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `userStats`
--

DROP TABLE IF EXISTS `userStats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `userStats` (
  `displayName` varchar(50) NOT NULL,
  `ehbWeeklyEhb` float DEFAULT '0',
  `chambers_of_xericWeeklyEHB` float DEFAULT '0',
  `chambers_of_xeric_challenge_modeWeeklyEHB` float DEFAULT '0',
  `the_corrupted_gauntletWeeklyEHB` float DEFAULT '0',
  `sol_hereditWeeklyEHB` float DEFAULT '0',
  `theatre_of_bloodWeeklyEHB` float DEFAULT '0',
  `theatre_of_blood_hard_modeWeeklyEHB` float DEFAULT '0',
  `tombs_of_amascut_expertWeeklyEHB` float DEFAULT '0',
  `tzkal_zukWeeklyEHB` float DEFAULT '0',
  `tztok_jadWeeklyEHB` float DEFAULT '0',
  `doom_of_mokhaiotlWeeklyEHB` float DEFAULT NULL,
  PRIMARY KEY (`displayName`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `userId` bigint(20) NOT NULL,
  `displayName` varchar(32) NOT NULL,
  `mainRSN` varchar(15) DEFAULT NULL,
  `altRSN` varchar(15) DEFAULT NULL,
  `rankId` int(11) NOT NULL,
  `points` int(10) unsigned NOT NULL,
  `isActive` bit(1) NOT NULL DEFAULT b'0',
  `joinDate` date DEFAULT NULL,
  `leaveDate` date DEFAULT NULL,
  `referredBy` varchar(500) DEFAULT NULL,
  `birthday` date DEFAULT NULL,
  `diaryPoints` int(11) DEFAULT '0',
  `masterDiaryPoints` int(11) DEFAULT '0',
  `diaryTierClaimed` int(11) DEFAULT '0',
  `nationality` varchar(5) DEFAULT 'AQ',
  `customQuote` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`userId`),
  KEY `u_uid` (`userId`),
  KEY `users_ibfk_1` (`rankId`),
  CONSTRAINT `users_ibfk_1` FOREIGN KEY (`rankId`) REFERENCES `ranks` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vcTypes`
--

DROP TABLE IF EXISTS `vcTypes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vcTypes` (
  `id` int(11) NOT NULL,
  `action` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vcmonthstats`
--

DROP TABLE IF EXISTS `vcmonthstats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vcmonthstats` (
  `year` int(11) NOT NULL,
  `month` int(11) NOT NULL,
  `hoursspent` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `vctracker`
--

DROP TABLE IF EXISTS `vctracker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vctracker` (
  `Id` int(11) NOT NULL AUTO_INCREMENT,
  `userId` bigint(20) NOT NULL,
  `channelId` bigint(20) DEFAULT '0',
  `status` int(11) NOT NULL,
  `datetime` datetime NOT NULL,
  PRIMARY KEY (`Id`),
  KEY `userId_idx` (`userId`),
  KEY `vcAction_idx` (`status`),
  CONSTRAINT `userId` FOREIGN KEY (`userId`) REFERENCES `users` (`userId`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `vcAction` FOREIGN KEY (`status`) REFERENCES `vcTypes` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1145184 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wiseoldmannamechanges`
--

DROP TABLE IF EXISTS `wiseoldmannamechanges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `wiseoldmannamechanges` (
  `latestnamechangeid` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'sanity2'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-12-29 19:25:32
