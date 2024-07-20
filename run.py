import uvicorn

def run():
    if __name__ == "__main__":
        uvicorn.run("main:app", reload=True)

run()