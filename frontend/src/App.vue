<template>
  <div id="app">
    <b-container fluid class="bv-main m-2">
      <Header />
      <TopToolbar
              :config="config"
              :configs_list="configs_list"
              v-on:save_config="saveConfig"
              v-on:load_config="loadConfig"
              v-on:delete_config="deleteConfig"
              v-on:deploy_config="deployConfig"
              class="my-2"
      />
      <b-row class="h-75">
        <b-col cols="4" class="tree-col">
          <TreeView
                  :config="config"
                  v-on:update_config="updateConfig"
                  v-on:delete_node="deleteNode"
                  v-on:add_node="isAdd = true"
          />
        </b-col>
        <b-col cols="8" class="node-col">
          <NodeView
                  :config="config"
                  :current_node="current_node"
                  :isAdd="isAdd"
                  v-on:cancel_add="isAdd = false"
                  v-on:update_config="updateConfig"
                  v-on:send_node_update="sendNodeUpdate"
          />
        </b-col>
      </b-row>
      <b-row>
        <Report
          :reports="reports"
          v-on:load_config="loadConfig"
        />
      </b-row>
    </b-container>
  </div>
</template>

<script>
  import Header from './components/Header.vue'
  import NodeView from './components/NodeView.vue'
  import TreeView from "./components/TreeView";
  import Report from "./components/Report";
  import TopToolbar from "@/components/TopToolbar";
  import axios from "axios";

  export default {
    name: 'App',

    components: {
      TreeView,
      Header,
      NodeView,
      Report,
      TopToolbar
    },

    data: function() {
      return {
        config: {},
        current_node: {},
        isAdd: false,
        reports: [],
        configs_list: [],
        server: {},
      }
    },

    methods: {

      updateConfig: function() {
        if (!(Object.keys(this.config).length === 0 && this.config.constructor === Object)) {
          axios.get("/v1/configs/" + this.config.name)
                  .then(response => {
                    this.config = response.data;
                  })
        }
      },

      updateCurrentNode(node) {
        this.current_node = node;
      },

      sendNodeUpdate(node) {
        if (this.isAdd) {
          axios.post(
            "/v1/configs/" + this.config.name + "/trees/" + this.current_node.id,
            node
          ).then(response => {
            this.reports = response.data
          })
        } else {
          axios.put(
            "/v1/configs/" + this.config.name + "/trees/" + this.current_node.id ,
            node
          ).then(response => {
            this.reports = response.data
          })
        }
        this.isAdd = false;
        this.updateConfig();
      },

      deleteNode() {
        if (this.current_node) {
          axios.delete(
            "/v1/configs/" + this.config.name + "/trees/" + this.current_node.id
          ).then(response => {
            this.reports = response.data;
            this.updateConfig();
          })
        }
        this.updateConfig();
      },

      loadConfigsList() {
        axios.get(
        "/v1/configs"
        ).then(response => {
          this.configs_list = response.data
        })
      },

      saveConfig(name) {
        this.config.name = name;
        axios.post(
          "/v1/configs",
          {config: this.config}
        ).then(response => {
          if (response.status === 200) {
            this.updateConfig();
            this.loadConfigsList();
          }
        })
      },

      deployConfig(address) {
        this.saveConfig(this.config.name);

        axios.put(
          "/v1/configs/" + this.config.name,
          {server: address}
        )
      },

      loadConfig(name) {
        axios.get(
          "/v1/configs/" + name
        ).then(response => {
          if (response.status === 200) {
            this.config = response.data
          }
        })
      },

      deleteConfig(name) {
        axios.delete(
          "/v1/configs/" + name,
        ).then(response => {
          if (response.status === 200) {
            this.updateConfig();
            this.loadConfigsList();
          }
        })
      }
    },

    watch: {
      current_node: function () {
        this.isAdd = false
      }
    },

    mounted() {
      this.loadConfigsList();
      this.updateConfig();
    }
  }
</script>

<style>
  #app {
    font-family: Avenir, Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-align: center;
    color: #2c3e50;
    margin-top: 60px;
  }

  .bv-main {
    height: 100vh;
  }

  .tree-col {
    border: 1px solid #ccc;
    border-radius: 16px;
  }

  .node-col {
    background-color: white;
  }

</style>
