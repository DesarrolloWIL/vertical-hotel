/* @odoo-module */

import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {useState} from "@odoo/owl";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
const {onWillUpdateProps} = owl;

export class RoomReservationWidget extends Component {
    static template = "RoomSummary";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        super.setup();
        console.log(this);
        this.actionService = useService("action");
        this.state = useState({
            date_to: false,
            date_from: false,
            summary_header: this.parseData(this.props.record.data.summary_header),
            room_summary: this.parseData(this.props.record.data.room_summary),
        });

        onWillUpdateProps((nextProps) => {
            this.state.summary_header = this.parseData(nextProps.record.data.summary_header);
            this.state.room_summary = this.parseData(nextProps.record.data.room_summary);
        });
    }
    
    parseData(data) {
        if (!data) return [];
        try {
            return JSON.parse(data);
        } catch (e) {
            console.error("Error parsing JSON:", e);
            return [];
        }
    }
    
    resize() {
        return this;
    }
    
    async load_form(room_id, date) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "quick.room.reservation",
            views: [[false, "form"]],
            target: "new",
            context: {
                room_id: room_id,
                date: date,
                default_adults: 1,
                summary_id: this.props.record.resId,
            },
        });
    }
}

export const roomReservationWidget = {
    component: RoomReservationWidget,
    supportedTypes: ["text"],
};

registry.category("fields").add("Room_Reservation", roomReservationWidget);





