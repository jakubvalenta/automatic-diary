function getRandomInt(max) {
    return Math.floor(Math.random() * Math.floor(max));
}

function parsePoints(s) {
    return s.trim().split(' ').map(coords => coords.split(',').map(coord => parseFloat(coord)));
}

function formatPoints(points) {
    return points.map(coords => coords.join(',')).join(' ');
}

var trs = Array.from(document.querySelectorAll('tbody tr'));
console.log(trs);
var svg = document.getElementsByTagName('svg')[0];
var doc = document.documentElement;
svg.setAttribute('viewBox', [0, 0, 1, doc.clientHeight].join(' '));
var line = document.getElementsByTagName('polyline')[0];
var oldPoints = parsePoints(line.getAttribute('points'));
console.log(oldPoints);
var newPoints = oldPoints.map(([x, y], i) => [x, trs[i].offsetTop]);
line.setAttribute('points', formatPoints(newPoints));
