var express = require("express");
var app = express();

app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.get("/app-second", function (req, res, next) {
  res.send({ title: "Express", application: "Application 2" });
});
app.listen(4000, () => console.log("Running on http://localhost:4000"));
