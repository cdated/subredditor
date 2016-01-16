function graph(data) {
    var width = Math.max(document.documentElement.clientWidth, window.innerWidth || 0);
    var height = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
    // Add whitespace
    width -= 20;
    height -= 100;

    var force = d3.layout.force()
        .size([width, height])
        .linkDistance(60)
        .charge(-2000)
        .gravity(0.1)
        .on("tick", tick);

    var svg = d3.select("#graph").append("svg")
        .attr("width", width)
        .attr("height", height)
        .attr('viewBox', '0 0 ' + Math.min(width, height) + ' ' + Math.min(width, height))
        .attr('preserveAspectRatio', 'xMinYMin')
        .attr("transform", "translate(" + Math.min(width, height) / 2 + "," + Math.min(width, height) / 2 + ")")
        .style("border", "1px solid black")
        .call(d3.behavior.zoom().on("zoom", function() {
            svg.attr("transform", "translate(" + d3.event.translate + ")" + " scale(" + d3.event.scale + ")")
        }))
        .append("g");

    var view = svg.append("view")
        .attr("id", "view")
        .attr("viewBox", "500 500 1000 1000");

    var path = svg.append("g").selectAll("path"),
        circle = svg.append("g").selectAll("circle"),
        hypertext = svg.append("g").selectAll("text");

    var marker = svg.append("defs").append("marker")
        .attr("id", "arrow")
        .attr("viewBox", "0 -5 10 10")
        .attr("refX", 15)
        .attr("refY", -1.5)
        .attr("markerWidth", 6)
        .attr("markerHeight", 6)
        .attr("orient", "auto")
        .append("path")
        .attr("d", "M0,-5L10,0L0,5");

    var nodes = data.nodes;
    var links = data.links;

    update(links);

    function update(links) {
        // Compute the distinct nodes from the links.
        links.forEach(function(link) {
            link.source = nodes[link.source];
            link.target = nodes[link.target];
        });

        force.nodes(nodes)
            .links(links)
            .start();

        // -------------------------------

        // Compute the data join. This returns the update selection.
        path = path.data(force.links());

        // Remove any outgoing/old paths.
        path.exit().remove();

        // Compute new attributes for entering and updating paths.
        path.enter().append("path")
            .attr("class", "link")
            .style("stroke", function(d) {
                var scheme = Please.make_scheme({
                    h: 145,
                    s: .7,
                    v: .6
                }, {
                    scheme_type: 'triadic',
                    format: 'rgb-string'
                });
                return d3.rgb(scheme[d.value - 1]);
            })
            //.attr("marker-end", "url(#arrow)");
            .attr("marker-end", "");

        // -------------------------------

        // Compute the data join. This returns the update selection.
        circle = circle.data(force.nodes());

        // Add any incoming circles.
        circle.enter().append("circle");

        // Remove any outgoing/old circles.
        circle.exit().remove();

        // Compute new attributes for entering and updating circles.
        circle.attr("r", function(d) {
                return d.subs;
            })
            .attr("is", function(d) {
                return "node-" + d.name
            })
            .style("fill", function(d) {
                var nodeColor = Please.make_color({
                    golden: true, //disable default
                    base_color: 'lightblue',
                    saturation: .7, //set your saturation manually
                    value: .8, //set your value manually
                    format: 'rgb-string'
                });
                return d3.rgb(nodeColor);
            })

        .call(force.drag);


        // Compute the data join. This returns the update selection.
        hypertext = hypertext.data(force.nodes());

        // Add any incoming texts.
        hypertext.enter().append("text")
            .append("a")
            //.attr("xlink:show", "new")
            .attr("target", "_blank");

        // Remove any outgoing/old texts.
        hypertext.exit().remove();

        // Compute new attributes for entering and updating texts.
        hypertext.attr("x", 0)
            .attr("y", ".31em")
            .select("a")
            .attr("xlink:href", function(d) {
                return "http://reddit.com/r/" + d.name;
            })
            .text(function(d) {
                return d.name;
            });
    }

    // Use elliptical arc path segments to doubly-encode directionality.
    function tick() {
        path.attr("d", linkArc);
        circle.attr("transform", transform);
        hypertext.attr("transform", transform);
    }

    function linkArc(d) {
        var dx = d.target.x - d.source.x,
            dy = d.target.y - d.source.y,
            dr = Math.sqrt(dx * dx + dy * dy);
        return "M" + d.source.x + "," + d.source.y + "A" + dr + "," + dr + " 0 0,1 " + d.target.x + "," + d.target.y;
    }

    function transform(d) {
        return "translate(" + d.x + "," + d.y + ")";
    }

};
