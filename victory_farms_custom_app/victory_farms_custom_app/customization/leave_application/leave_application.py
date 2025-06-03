from victory_farms_custom_app.victory_farms_custom_app.customization.leave_application.utils.additional_salary import create_additional_salary, create_reverse_jv

def on_submit(self, method):
    create_additional_salary(self)
    create_reverse_jv(self)