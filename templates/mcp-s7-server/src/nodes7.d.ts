declare module "nodes7" {
  interface Nodes7Options {
    port?: number;
    host?: string;
    rack?: number;
    slot?: number;
    debug?: boolean;
    localTSAP?: number;
    remoteTSAP?: number;
    timeout?: number;
    doNotOptimize?: boolean;
  }

  class NodeS7 {
    doNotOptimize?: boolean;
    initiateConnection(options: Nodes7Options, callback: (err?: any) => void): void;
    dropConnection(callback: () => void): void;
    setTranslationCB(callback: (tag: string) => string | undefined): void;
    addItems(tags: string | string[]): void;
    removeItems(tags: string | string[]): void;
    readAllItems(callback: (anythingBad: boolean, values: Record<string, any>) => void): void;
    writeItems(tags: string | string[], values: any, callback: (anythingBad: boolean) => void): void;
  }

  var nodes7: {
    new (): NodeS7;
    prototype: NodeS7;
  };

  export = nodes7;
}
