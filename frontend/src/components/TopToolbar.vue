<template>
    <div class="cb-toptoolbar">
        <b-row>
            <b-col class="m-2">
                <b-input-group prepend="Config" id="toptoolbar-load-config">
                    <b-form-select
                            id="toptoolbar-select-config"
                            v-model="selected_config"
                            :options="configs_list"
                    />
                    <template v-slot:append>
                        <b-button @click="loadConfig">Load</b-button>
                    </template>
                </b-input-group>
            </b-col>
            <b-col class="m-2">
                <b-input-group prepend="Name" id="toptoolbar-save-config">
                    <b-input
                            id="toptoolbar-name"
                            v-model="name"
                            type="text"
                    />
                    <template v-slot:append>
                        <b-button @click="saveConfig">Save</b-button>
                    </template>
                </b-input-group>
            </b-col>
            <b-col class="m-2">
                <b-input-group prepend="Config" id="toptoolbar-delete-config">
                    <b-form-select
                            id="toptoolbar-select-config"
                            v-model="delete_selected_config"
                            :options="configs_list"
                    />
                    <template v-slot:append>
                        <b-button @click="deleteConfig">Delete</b-button>
                    </template>
                </b-input-group>
            </b-col>
        </b-row>
        <b-input-group prepend="Server" id="toptoolbar-deploy-config" class="m-2">
                <b-input
                        id="toptoolbar-deploy-server"
                        v-model="server"
                        type="text"
                />
                <template v-slot:append>
                    <b-button @click="deployConfig">deploy</b-button>
                </template>
            </b-input-group>
    </div>
</template>

<script>
    export default {
        name: "TopToolbar",
        props: {
            config: Object,
            configs_list: Array
        },
        data() {
            return {
                name: '',
                selected_config: String,
                delete_selected_config: String,
                server: '',
            }
        },
        methods: {
            loadConfig() {
                this.$emit("load_config", this.selected_config)
            },
            saveConfig() {
                this.$emit("save_config", this.name)
            },
            deleteConfig() {
                this.$emit("delete_config", this.delete_selected_config)
            },
            deployConfig() {
                this.$emit("deploy_config", this.server)
            }
        },
        watch: {
            config: function () {
                this.name = this.config.name;
                this.selected_config = this.name;
            }
        }
    }
</script>

<style scoped>

</style>