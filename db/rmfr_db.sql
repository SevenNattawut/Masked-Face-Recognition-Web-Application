-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 28, 2023 at 05:54 PM
-- Server version: 10.4.28-MariaDB
-- PHP Version: 8.2.4

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `rmfr_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `commit_log`
--

CREATE TABLE `commit_log` (
  `id` int(11) NOT NULL,
  `commit_id` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
  `action` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `commit_log`
--

INSERT INTO `commit_log` (`id`, `commit_id`, `timestamp`, `action`) VALUES
(1, 1, '2023-04-28 05:57:11', '{\"type\": \"TRAIN\"}');

-- --------------------------------------------------------

--
-- Table structure for table `departments`
--

CREATE TABLE `departments` (
  `dep_id` int(11) NOT NULL,
  `dep_name` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `departments`
--

INSERT INTO `departments` (`dep_id`, `dep_name`) VALUES
(1, 'Student Council'),
(2, 'CPE'),
(3, 'CHE'),
(4, 'CE'),
(5, 'EE'),
(6, 'FIBO');

-- --------------------------------------------------------

--
-- Table structure for table `positions`
--

CREATE TABLE `positions` (
  `pos_id` int(11) NOT NULL,
  `pos_name` varchar(32) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `positions`
--

INSERT INTO `positions` (`pos_id`, `pos_name`) VALUES
(1, 'Manager'),
(2, 'Teacher'),
(3, 'Student'),
(4, 'Researcher');

-- --------------------------------------------------------

--
-- Table structure for table `user_account`
--

CREATE TABLE `user_account` (
  `id` int(11) NOT NULL,
  `pass_code` longtext NOT NULL,
  `is_admin` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `user_account`
--

INSERT INTO `user_account` (`id`, `pass_code`, `is_admin`) VALUES
(1, '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', 1),
(2, '', 0),
(3, '', 0);

-- --------------------------------------------------------

--
-- Table structure for table `user_images`
--

CREATE TABLE `user_images` (
  `id` int(11) NOT NULL,
  `last_update` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `user_images`
--

INSERT INTO `user_images` (`id`, `last_update`) VALUES
(1, '2023-04-28 05:05:33'),
(2, '2023-04-28 05:51:43'),
(3, '2023-04-28 05:51:43');

-- --------------------------------------------------------

--
-- Table structure for table `user_info`
--

CREATE TABLE `user_info` (
  `id` int(11) NOT NULL,
  `first_name` varchar(32) NOT NULL,
  `last_name` varchar(32) NOT NULL,
  `email` varchar(32) NOT NULL,
  `gender` varchar(32) NOT NULL,
  `pos_id` int(11) NOT NULL,
  `dep_id` int(11) NOT NULL,
  `birthday` date NOT NULL,
  `contact` longtext DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `user_info`
--

INSERT INTO `user_info` (`id`, `first_name`, `last_name`, `email`, `gender`, `pos_id`, `dep_id`, `birthday`, `contact`) VALUES
(1, 'Nattawut', 'Na Lumpoon', 'yochimi.20620@gmail.com', 'Male', 3, 2, '2000-05-25', 'test'),
(2, 'Pavat', 'Poonpinij', 'pavat@gmail.com', 'Male', 3, 2, '2001-06-13', NULL),
(3, 'Sirapop', 'Apananda', 'pun@gmail.com', 'Male', 3, 2, '2001-04-02', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `weekly_timestamp`
--

CREATE TABLE `weekly_timestamp` (
  `id` int(11) NOT NULL,
  `timestamp` timestamp NOT NULL DEFAULT current_timestamp(),
  `detected_user` longtext NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

--
-- Dumping data for table `weekly_timestamp`
--

INSERT INTO `weekly_timestamp` (`id`, `timestamp`, `detected_user`) VALUES
(1, '2023-04-28 06:09:43', '{\"id\": 1, \"name\": \"Nattawut Na Lumpoon\", \"position\": \"Student\", \"department\": \"CPE\"}');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `commit_log`
--
ALTER TABLE `commit_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `departments`
--
ALTER TABLE `departments`
  ADD PRIMARY KEY (`dep_id`);

--
-- Indexes for table `positions`
--
ALTER TABLE `positions`
  ADD PRIMARY KEY (`pos_id`);

--
-- Indexes for table `user_account`
--
ALTER TABLE `user_account`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `user_images`
--
ALTER TABLE `user_images`
  ADD KEY `id` (`id`);

--
-- Indexes for table `user_info`
--
ALTER TABLE `user_info`
  ADD KEY `id` (`id`),
  ADD KEY `pos_id` (`pos_id`),
  ADD KEY `dep_id` (`dep_id`);

--
-- Indexes for table `weekly_timestamp`
--
ALTER TABLE `weekly_timestamp`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `commit_log`
--
ALTER TABLE `commit_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `departments`
--
ALTER TABLE `departments`
  MODIFY `dep_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `positions`
--
ALTER TABLE `positions`
  MODIFY `pos_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `user_account`
--
ALTER TABLE `user_account`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `weekly_timestamp`
--
ALTER TABLE `weekly_timestamp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `user_images`
--
ALTER TABLE `user_images`
  ADD CONSTRAINT `user_images_ibfk_1` FOREIGN KEY (`id`) REFERENCES `user_account` (`id`);

--
-- Constraints for table `user_info`
--
ALTER TABLE `user_info`
  ADD CONSTRAINT `user_info_ibfk_1` FOREIGN KEY (`id`) REFERENCES `user_account` (`id`),
  ADD CONSTRAINT `user_info_ibfk_2` FOREIGN KEY (`pos_id`) REFERENCES `positions` (`pos_id`),
  ADD CONSTRAINT `user_info_ibfk_3` FOREIGN KEY (`dep_id`) REFERENCES `departments` (`dep_id`);

DELIMITER $$
--
-- Events
--
CREATE DEFINER=`root`@`localhost` EVENT `weekly_timestamp_delete` ON SCHEDULE EVERY 1 DAY STARTS '2023-04-29 00:00:00' ON COMPLETION NOT PRESERVE ENABLE DO DELETE FROM weekly_timestamp WHERE DATEDIFF(CURRENT_DATE, weekly_timestamp.timestamp) > 7$$

DELIMITER ;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
