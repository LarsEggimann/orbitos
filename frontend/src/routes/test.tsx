import { useQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import path from 'path'
import { ElectrometerService, ElectrometerState } from '~/generated'

export const Route = createFileRoute('/test')({
    component: RouteComponent,
})

function RouteComponent() {

    const myQuery = useQuery<ElectrometerState>({
        queryKey: ['electrometerState'],
        queryFn: async () => {
            const response = await ElectrometerService.electrometerGetElectrometerState({
                path: {
                    device_id: 'electrometer_1'
                }
            })
            if (!response.data) {
                throw new Error(`Failed to fetch electrometer state: ${response.status} ${response.error}`)
            }
            return response.data
        }
    })

    return <div>Hello "/test"!
        <div>
            <h2>Electrometer State</h2>
            {myQuery.isLoading && <p>Loading...</p>}
            {myQuery.isError && <p>Error: {myQuery.error.message}</p>}
            {myQuery.isSuccess && (
                <pre>{JSON.stringify(myQuery.data, null, 2)}</pre>
            )}
        </div>



    </div>
}
