function getRandomInt(max) {
    return Math.floor(Math.random() * Math.floor(max));
}

var trs = document.getElementsByTagName('tr');
var points = Array.from(trs).map(tr => [tr.offsetTop, getRandomInt(600)]);

var svg = document.getElementsByTagName('svg')[0];
var doc = document.documentElement;
svg.setAttribute('viewBox', [0, 0, doc.clientWidth, doc.clientHeight].join(' '));
var line = document.getElementsByTagName('polyline')[0];
line.setAttribute('points', points.map(([x, y]) => [y, x].join(',')).join(' '));
