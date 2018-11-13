USE photoshare;

CREATE TABLE `album_id_name` (
  `album_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `user_id` int(11) NOT NULL,
  `date_created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`album_id`)
);

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `fname` varchar(40) DEFAULT NULL,
  `lname` varchar(40) DEFAULT NULL,
  `DoB` date DEFAULT NULL,
  `prof_pic` longblob,
  `email` varchar(50) DEFAULT NULL,
  `password` varchar(15) DEFAULT NULL,
  `gender` varchar(10) DEFAULT NULL,
  `bio` varchar(500) DEFAULT '',
  `hometown` varchar(85) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
);

CREATE TABLE `albums` (
  `album_id` int(11) NOT NULL DEFAULT '0',
  `name` varchar(100) DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `photo_id` int(11) DEFAULT NULL,
  `date_created` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  KEY `user_id` (`user_id`),
  CONSTRAINT `albums_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
);

CREATE TABLE `photos` (
  `photo_id` int(11) NOT NULL AUTO_INCREMENT,
  `album_id` int(11) DEFAULT NULL,
  `caption` varchar(250) DEFAULT '',
  `user_id` int(11) DEFAULT NULL,
  `imgdata` longblob,
  `comment_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`photo_id`),
  KEY `album_id` (`album_id`),
  KEY `upid_idx` (`user_id`),
  CONSTRAINT `photos_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ;

CREATE TABLE `comments` (
 `comment_id` int(11) NOT NULL AUTO_INCREMENT,
 `text` varchar(200) DEFAULT NULL,
 `user_id` int(11) DEFAULT '0',
 `photo_id` int(11) NOT NULL DEFAULT '0',
 `date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
 PRIMARY KEY (`comment_id`),
 KEY `user_id` (`user_id`)
);

CREATE TABLE `friends` (
 `user_id` int(11) NOT NULL DEFAULT '0',
 `friend_id` int(11) DEFAULT '0'
);

CREATE TABLE `tags` (
 `word` varchar(200) NOT NULL,
 `photo_id` int(11) DEFAULT NULL,
 `user_id` int(11) DEFAULT NULL,
 `tag_id` int(11) NOT NULL,
 KEY `photo_id` (`photo_id`),
 KEY `user_id` (`user_id`),
 CONSTRAINT `tags_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
);

CREATE TABLE `tag_id_word` (
  `tag_id` int(11) NOT NULL AUTO_INCREMENT,
  `word` varchar(200) NOT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`tag_id`)
);

CREATE TABLE `likes` (
  `photo_id` int(11) DEFAULT '0',
  `user_id` int(11) DEFAULT '0'
);


INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
