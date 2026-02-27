from decimal import Decimal
from unittest.mock import MagicMock

from ocmonitor.ui.tables import TableFormatter


def test_live_dashboard_parent_row_uses_workflow_total_tokens():
    formatter = TableFormatter()

    parent = MagicMock()
    parent.display_title = "Parent Session"
    parent.duration_percentage = 20.0
    parent.total_tokens.total = 150
    parent.calculate_total_cost.return_value = Decimal("1.00")

    sub_agent_a = MagicMock()
    sub_agent_a.display_title = "Sub A"
    sub_agent_a.total_tokens.total = 300
    sub_agent_a.calculate_total_cost.return_value = Decimal("2.00")

    sub_agent_b = MagicMock()
    sub_agent_b.display_title = "Sub B"
    sub_agent_b.total_tokens.total = 50
    sub_agent_b.calculate_total_cost.return_value = Decimal("0.50")

    hierarchy = {
        "root_sessions": [
            {
                "session": parent,
                "sub_agents": [sub_agent_a, sub_agent_b],
            }
        ]
    }

    table = formatter.create_live_dashboard_table(hierarchy, pricing_data={})

    # Token column (index 1) should show parent + all sub-agent tokens.
    assert table.columns[1]._cells[0] == "500"
