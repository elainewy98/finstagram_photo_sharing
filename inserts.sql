-- Section B: Inserting values into the tables

INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("AA", SHA2('AA', 256),"Ann", "Anderson", "ann.jpg", "I love dogs");
INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("BB", SHA2('BB', 256),"Bob", "Baker", "bob.jpg", "My dad is Bob Ross");
INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("CC", SHA2('CC', 256), "Cathy", "Chang", "cathy.jpg", "Cheerleading is my favorite sport");
INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("DD", SHA2('DD', 256),"David", "Davidson", "david.jpg", "I'm a proud father of 5");
INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("EE", SHA2('EE', 256),'Ellen', 'Ellenberg', "ellen.jpg", "I want to be like Ellen Degeneres");
INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("FF", SHA2('FF', 256),'Fred', 'Fox', "fred.jpg", "My name is Fred");
INSERT INTO person(username,password,fname,lname,avatar,bio) VALUES ("GG", SHA2('GG', 256),'Gina', 'Gupta', "gina.jpg", "Gina from Brooklyn 99 is my role model");


INSERT INTO closefriendgroup VALUES ("family","AA");
INSERT INTO closefriendgroup VALUES ("family", "BB");
INSERT INTO closefriendgroup VALUES ("roommates","AA");
INSERT INTO closefriendgroup VALUES ("partying","DD");

INSERT INTO belong VALUES ("family","AA", "AA");
INSERT INTO belong VALUES ("family","AA", "BB");
INSERT INTO belong VALUES ("family","AA", "DD");
INSERT INTO belong VALUES ("family","BB", "BB");
INSERT INTO belong VALUES ("roommates","AA", "AA");
INSERT INTO belong VALUES ("roommates","AA", "GG");
INSERT INTO belong VALUES ("partying","DD", "DD");
INSERT INTO belong VALUES ("partying","DD", "AA");

INSERT INTO follow VALUES ("CC","AA",0);
INSERT INTO follow VALUES ("DD","AA",1);
INSERT INTO follow VALUES ("AA","DD",1);
INSERT INTO follow VALUES ("BB","AA",1);
INSERT INTO follow VALUES ("AA","BB",1);
INSERT INTO follow VALUES ("BB","FF",1);
INSERT INTO follow VALUES ("FF","BB",0);
INSERT INTO follow VALUES ("DD","BB",0);



INSERT INTO photo(photoOwner,timestamp,filePath,allFollowers,caption) VALUES ("AA", timestamp("2018-01-19", "03:14:07"),"tesla.jpg",1,"Teslas are amazing!");
INSERT INTO photo(photoOwner,timestamp,filePath,allFollowers,caption) VALUES ("AA", timestamp("2018-01-19", "03:14:08"),"hawaii.jpg",0,"Hawaii is a paradise.");
INSERT INTO photo(photoOwner,timestamp,filePath,allFollowers,caption) VALUES ("FF", timestamp("2018-01-19", "04:14:08"),"worldcup.jpg",1,"World Cup SZN");






INSERT INTO share VALUES ("family","AA", 2);

INSERT INTO tag VALUES ("DD",1,0);
INSERT INTO tag VALUES ("DD",2,1);