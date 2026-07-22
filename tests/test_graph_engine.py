"""Tests for GraphOrchestrator."""

from jig.orchestrator.graph_engine import GraphOrchestrator, GraphNode, GraphEdge, EdgeType, GraphRuntimeError


class TestGraphOrchestrator:
    def test_add_node(self):
        g = GraphOrchestrator()
        g.add_node(GraphNode(name="a"))
        assert "a" in g._nodes

    def test_add_edge(self):
        g = GraphOrchestrator()
        g.add_node(GraphNode(name="a"))
        g.add_node(GraphNode(name="b"))
        g.add_edge(GraphEdge(source="a", target="b"))
        assert len(g._edges) == 1

    def test_add_edge_missing_source(self):
        g = GraphOrchestrator()
        g.add_node(GraphNode(name="b"))
        import pytest
        with pytest.raises(GraphRuntimeError):
            g.add_edge(GraphEdge(source="a", target="b"))

    def test_linear_execution(self):
        g = GraphOrchestrator()
        g.add_node(GraphNode(name="start"))
        g.add_node(GraphNode(name="middle"))
        g.add_node(GraphNode(name="end"))
        g.add_edge(GraphEdge(source="start", target="middle"))
        g.add_edge(GraphEdge(source="middle", target="end"))
        result = g.run("start")
        assert result is not None

    def test_conditional_branch(self):
        g = GraphOrchestrator()
        g.add_node(GraphNode(name="start"))
        g.add_node(GraphNode(name="if_true"))
        g.add_node(GraphNode(name="if_false"))
        g.add_edge(GraphEdge(source="start", target="if_true", edge_type=EdgeType.CONDITIONAL,
                             condition=lambda ctx: ctx.get("val", False)))
        g.add_edge(GraphEdge(source="start", target="if_false", edge_type=EdgeType.DEFAULT))
        result = g.run("start", {"val": True})
        assert result is not None

    def test_start_node_not_found(self):
        g = GraphOrchestrator()
        import pytest
        with pytest.raises(GraphRuntimeError):
            g.run("nonexistent")

    def test_get_graph_info(self):
        g = GraphOrchestrator()
        g.add_node(GraphNode(name="a"))
        g.add_node(GraphNode(name="b"))
        g.add_edge(GraphEdge(source="a", target="b"))
        info = g.get_graph_info()
        assert "nodes" in info
        assert "edges" in info
